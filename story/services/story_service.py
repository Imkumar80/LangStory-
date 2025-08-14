import os
import re
import logging
from io import BytesIO
from typing import List, Dict, Any

import requests
from PIL import Image
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from django.conf import settings


logger = logging.getLogger('story')


class GenerationError(Exception):
    pass


# Load env from project root once (safeguard if not already loaded by settings)
load_dotenv()


def _extract_key_objects(user_prompt: str) -> List[str]:
    words = re.findall(r'\b\w+\b', user_prompt)
    ignore = {"and", "the", "a", "an", "to", "are", "is", "of", "on", "in", "with", "for", "but"}
    objects = [w for w in words if w.lower() not in ignore]
    # Remove duplicates preserving order
    seen = set()
    unique_objects = []
    for word in objects:
        lower = word.lower()
        if lower not in seen:
            seen.add(lower)
            unique_objects.append(word)
    return unique_objects


class StoryOutput(BaseModel):
    short_story: str = Field(description="A 3-paragraph short story in Studio Ghibli's warm, imaginative tone.")
    character_description: str = Field(description=(
        "A detailed visual description of ALL main characters, each listed separately. "
        "Describe species, appearance, clothing, accessories, posture, expression. "
        "They should be standing on a plain white background for clean separation."
    ))
    background_description: str = Field(description=(
        "A detailed visual description of the environment in Studio Ghibli art style. "
        "Include lighting, atmosphere, objects, and setting details. There should be No characters in this image ."
    ))


def _create_story_chain():
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)
    output_parser = PydanticOutputParser(pydantic_object=StoryOutput)

    prompt_template = (
        """
        You are a creative writer and concept artist.

        The user will provide a creative idea.  
        From that idea, generate:
        1. A short story (3 paragraphs, Studio Ghibli style).
        2. A detailed description of ALL characters, each listed separately, plain white background.
        3. A detailed background description.

        RULES:
        - You MUST include all key characters and objects from the user's prompt in every part of your output.
        - For objects, describe their appearance, size, color, and exact placement so they are easy to visualize in artwork.
        - Maintain whimsical, heartfelt storytelling.

        Key objects/characters to include: {key_objects}

        {format_instructions}

        USER PROMPT: {user_prompt}
        """
    )

    prompt = ChatPromptTemplate.from_template(template=prompt_template)
    return prompt | model | output_parser


def _create_image_prompt_refiner_chain():
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
    prompt_template = (
        """
        You are an expert AI image prompt engineer.
        Convert the description into a concise, effective prompt for a text-to-image model.

        REQUIREMENTS:
        - Must include: {style_context}
        - Preserve all characters exactly as described (species, clothing, posture, accessories).
        - Include all important objects: {key_objects}
        - Keep perspective, lighting, and color palette consistent.
        - Output should be a single line of comma-separated keywords.

        DESCRIPTION: {description}

        CONCISE PROMPT:
        """
    )

    prompt = ChatPromptTemplate.from_template(prompt_template)
    return prompt | model | StrOutputParser()


def _extract_style_context() -> str:
    return (
        "Studio Ghibli art style, watercolor painting, soft pastel tones, "
        "cinematic lighting, highly detailed, masterpiece, consistent perspective, "
        "natural integration between characters and environment"
    )


def _generate_image_from_hf(prompt: str, model_id: str = "black-forest-labs/FLUX.1-dev") -> bytes | None:
    api_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
    if not api_token:
        logger.error("HUGGINGFACEHUB_API_TOKEN not set")
        return None

    headers = {"Authorization": f"Bearer {api_token}"}
    api_url = f"https://api-inference.huggingface.co/models/{model_id}"

    logger.info("Sending prompt to Hugging Face model", extra={"model_id": model_id})

    try:
        response = requests.post(api_url, headers=headers, json={"inputs": prompt}, timeout=60)
        response.raise_for_status()

        content_type = response.headers.get('content-type', '')
        if 'application/json' in content_type:
            data = response.json()
            if 'error' in data:
                logger.error("HF API error", extra={'error': data['error']})
                return None
        return response.content
    except requests.exceptions.Timeout:
        logger.exception("HF request timed out")
        return None
    except requests.exceptions.RequestException:
        logger.exception("HF request error")
        return None
    except Exception:
        logger.exception("Unexpected error generating image from HF")
        return None


def _save_image(image_bytes: bytes | None, filepath: str) -> bool:
    if not image_bytes:
        logger.error("No image data to save", extra={"filepath": filepath})
        return False
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        img = Image.open(BytesIO(image_bytes))
        img.save(filepath, "PNG")
        logger.info("Saved image", extra={"filepath": filepath})
        return True
    except Exception:
        logger.exception("Error saving image", extra={"filepath": filepath})
        return False


def generate_story_and_images(user_prompt: str) -> Dict[str, Any]:
    # Check API keys early
    if not os.getenv("GOOGLE_API_KEY"):
        raise GenerationError("GOOGLE_API_KEY not found. Check your .env file.")
    if not os.getenv("HUGGINGFACEHUB_API_TOKEN"):
        raise GenerationError("HUGGINGFACEHUB_API_TOKEN not found. Check your .env file.")

    key_objects = _extract_key_objects(user_prompt)
    style_context = _extract_style_context()
    logger.info("Key objects detected", extra={"key_objects": key_objects})

    story_chain = _create_story_chain()
    refiner_chain = _create_image_prompt_refiner_chain()

    try:
        story_data: StoryOutput = story_chain.invoke({
            "user_prompt": user_prompt,
            "key_objects": ", ".join(key_objects),
            "format_instructions": PydanticOutputParser(pydantic_object=StoryOutput).get_format_instructions()
        })
    except Exception as e:
        logger.exception("Error generating story")
        raise GenerationError(f"Error generating story: {e}")

    # Prepare image prompts
    full_scene_desc = (
        f"\nOriginal idea: \"{user_prompt}\".\n"
        f"Scene includes: {story_data.character_description.replace('on a plain white background', 'naturally integrated into the scene')}.\n"
        f"Background: {story_data.background_description}.\n"
        f"All important objects must be clearly visible: {', '.join(key_objects)}.\n"
    )

    refined_full_prompt = refiner_chain.invoke({
        "description": full_scene_desc,
        "style_context": style_context,
        "key_objects": ", ".join(key_objects)
    })

    char_prompt = refiner_chain.invoke({
        "description": f"{story_data.character_description}, isolated, white background, character study.",
        "style_context": style_context,
        "key_objects": ", ".join(key_objects)
    })

    bg_prompt = refiner_chain.invoke({
        "description": f"{story_data.background_description}, no characters, environment only.",
        "style_context": style_context,
        "key_objects": ", ".join(key_objects)
    })

    # File paths (under MEDIA_ROOT)
    media_root = os.getenv('MEDIA_ROOT')  # optional override
    base_media_dir = media_root or str(settings.MEDIA_ROOT)
    full_scene_path = os.path.join(base_media_dir, 'generated', 'full_scene.png')
    character_path = os.path.join(base_media_dir, 'generated', 'character.png')
    background_path = os.path.join(base_media_dir, 'generated', 'background.png')

    _save_image(_generate_image_from_hf(refined_full_prompt), full_scene_path)
    _save_image(_generate_image_from_hf(char_prompt), character_path)
    _save_image(_generate_image_from_hf(bg_prompt), background_path)

    return {
        'prompt': user_prompt,
        'key_objects': key_objects,
        'short_story': story_data.short_story,
        'character_description': story_data.character_description,
        'background_description': story_data.background_description,
        'full_scene_image': '/media/generated/full_scene.png',
        'character_image': '/media/generated/character.png',
        'background_image': '/media/generated/background.png',
    }


