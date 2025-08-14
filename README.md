
# LangChain + Django AI Story and Image Generation WebInterface

LangStory is a Django-based web application that uses **LangChain** to generate AI-powered stories and images from user prompts.  



## Run Locally

Clone the project

```bash
  git clone https://github.com/Imkumar80/LangStory-.git
```

Go to the project directory

```bash
  cd LangStory
```
Create a Virtual Environment
```bash
  python -m venv .venv
  .venv\Scripts\Activate
```
Install dependencies

```bash
  pip install -r requirements.txt
```
Set Environment Variables
```bash
  Create a .env file in the project root and add:

GOOGLE_API_KEY='Your_API_Key_here'
HUGGINGFACEHUB_API_TOKEN='Your_API_Key_here'

```

Start the server
```bash
  python manage.py migrate
  python manage.py runserver
```


## Screenshots




## Documentation

# Prompt Engineering Documentation

## Story Generator

### Overview

I have used a sophisticated prompt engineering approach to generate cohesive Studio Ghibli-style stories with accompanying artwork. The process involves multiple stages of prompt refinement and specialized chains for different content types.

---

## Story Generation Prompt Structure

### Primary Story Prompt Template

The core story generation uses a structured prompt template that ensures consistency and adherence to Studio Ghibli aesthetics:

python

`prompt_template = """
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
"""`

### Key Components Breakdown

### 1. Role Definition

- **Purpose**: Establishes the AI as both a "creative writer and concept artist"
- **Impact**: Creates dual expertise for both narrative and visual content generation

### 2. Output Structure Requirements

The prompt explicitly requests three distinct outputs:

- **Short Story**: 3 paragraphs in Studio Ghibli style
- **Character Description**: Detailed visual descriptions with white background specification
- **Background Description**: Environment details without characters

### 3. Constraint Rules

- **Inclusion Mandate**: Forces inclusion of all key objects/characters
- **Visual Specificity**: Requires appearance, size, color, and placement details
- **Tone Consistency**: Maintains "whimsical, heartfelt storytelling"

### 4. Dynamic Variables

- `{key_objects}`: Extracted keywords from user input
- `{format_instructions}`: Pydantic schema formatting
- `{user_prompt}`: Original user request

### Key Object Extraction Logic

python

`def _extract_key_objects(user_prompt: str) -> List[str]:
    words = re.findall(r'\b\w+\b', user_prompt)
    ignore = {"and", "the", "a", "an", "to", "are", "is", "of", "on", "in", "with", "for", "but"}
    objects = [w for w in words if w.lower() not in ignore]
    *# Remove duplicates preserving order*
    seen = set()
    unique_objects = []
    for word in objects:
        lower = word.lower()
        if lower not in seen:
            seen.add(lower)
            unique_objects.append(word)
    return unique_objects`

**Strategy**:

- Extracts all meaningful words while filtering common articles/prepositions
- Preserves order and removes duplicates
- Ensures visual consistency across all generated content

---

## Image Prompt Construction System

### Two-Stage Refinement Process

The system uses a specialized refinement chain to convert descriptive text into optimized image generation prompts.

### Image Prompt Refiner Template

python

`prompt_template = """
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
"""`

### Style Context Foundation

python

`def _extract_style_context() -> str:
    return (
        "Studio Ghibli art style, watercolor painting, soft pastel tones, "
        "cinematic lighting, highly detailed, masterpiece, consistent perspective, "
        "natural integration between characters and environment"
    )`

**Design Philosophy**:

- Establishes consistent visual identity across all images
- Balances artistic style with technical quality descriptors
- Ensures environmental harmony between elements

---

## Three Image Generation Approaches

### 1. Full Scene Image

**Construction Process**:

python

`full_scene_desc = (
    f"\nOriginal idea: \"{user_prompt}\".\n"
    f"Scene includes: {story_data.character_description.replace('on a plain white background', 'naturally integrated into the scene')}.\n"
    f"Background: {story_data.background_description}.\n"
    f"All important objects must be clearly visible: {', '.join(key_objects)}.\n"
)`

**Key Strategies**:

- **Context Preservation**: Maintains connection to original user intent
- **Background Replacement**: Dynamically replaces "white background" with scene integration
- **Object Visibility**: Explicitly ensures all key elements are prominent
- **Narrative Cohesion**: Combines character and environment descriptions

### 2. Character-Only Image

**Construction Process**:

python

`char_prompt = refiner_chain.invoke({
    "description": f"{story_data.character_description}, isolated, white background, character study.",
    "style_context": style_context,
    "key_objects": ", ".join(key_objects)
})`

**Design Decisions**:

- **Isolation Strategy**: Uses white background for clean character separation
- **Study Format**: Frames as "character study" for artistic focus
- **Detail Preservation**: Maintains all character-specific details from story generation

### 3. Background-Only Image

**Construction Process**:

python

`bg_prompt = refiner_chain.invoke({
    "description": f"{story_data.background_description}, no characters, environment only.",
    "style_context": style_context,
    "key_objects": ", ".join(key_objects)
})`

**Environmental Focus**:

- **Character Exclusion**: Explicitly removes characters for pure environment
- **Object Integration**: Maintains story-relevant objects in the scene
- **Atmospheric Emphasis**: Allows full focus on lighting, mood, and setting

---

## Prompt Engineering Best Practices Implemented

### 1. Structured Output Control

- **Pydantic Models**: Enforces consistent output structure
- **Field Descriptions**: Provides clear guidance for each output component
- **Validation**: Ensures all required elements are present

### 2. Context Preservation

- **Key Object Tracking**: Maintains story elements across all outputs
- **Style Consistency**: Applies uniform aesthetic standards
- **Narrative Coherence**: Links visual and textual elements

### 3. Constraint Management

- **Explicit Requirements**: Clear rules prevent deviation from intended style
- **Format Specifications**: Ensures compatibility with image generation models
- **Quality Control**: Built-in checks for completeness and consistency

### 4. Error Handling

- **Graceful Failures**: Comprehensive error catching and logging
- **Resource Validation**: Early API key checking
- **Recovery Strategies**: Informative error messages for debugging

---

## Usage Patterns and Optimization

### Effective Input Patterns

- **Descriptive Prompts**: Rich detail produces better key object extraction
- **Narrative Elements**: Story-like inputs work better than simple descriptions
- **Character Focus**: Prompts with clear protagonists generate more cohesive results

### Model Temperature Settings

- **Story Generation**: `temperature=0.7` for creative variety
- **Prompt Refinement**: `temperature=0` for consistent technical conversion

### Optimization Strategies

- **Caching**: Reuses refined prompts for similar requests
- **Batch Processing**: Generates all images in parallel where possible
- **Quality Validation**: Checks image generation success before proceeding

---

## Advanced Prompt Engineering Techniques

### Dynamic Context Adaptation

The system adapts prompts based on content analysis rather than using static templates, ensuring each generation is optimized for the specific input.

### Multi-Modal Consistency

By using the same key objects across story, character, and background generation, the system maintains thematic and visual consistency across all outputs.

### Layered Refinement

The two-stage refinement process (descriptive → technical) ensures that artistic vision is preserved while optimizing for AI model performance.

This documentation provides a comprehensive understanding of how prompt engineering drives the entire story and image generation pipeline, enabling consistent, high-quality Studio Ghibli-style content creation.


## Sample_Output
Enter your story idea: cat and dog are planning to eat mango

🔍 Key objects/characters detected: ['cat', 'dog', 'planning', 'eat', 'mango']

- STORY 
Whiskers twitched, a fluffy ginger cat named Marmalade perched on a weathered wooden crate. Below, Barnaby, a scruffy terrier with one ear perpetually flopped, held a ripe, golden mango aloft. Their grand plan, hatched under the shade of a sprawling mango tree, was simple: a shared feast. Marmalade, ever the strategist, had meticulously mapped out the perfect bite-sized portions using twigs and pebbles, ensuring equitable distribution.

Barnaby, tail wagging furiously, eyed the mango with uncontainable glee. He’d sniffed out this treasure in the nearby orchard, a juicy reward for their collaborative efforts.  Their friendship, forged in playful chases and shared naps, was about to be cemented with the sweetest of treats.  The air hummed with anticipation, a symphony of chirping crickets and rustling leaves.

With a shared glance, a silent agreement passed between the two.  Marmalade delicately took the first bite, the sweet juice dripping down her chin. Barnaby, with a happy yelp, followed suit, his small teeth sinking into the fragrant flesh.  The mango, a symbol of their bond, disappeared in a flurry of happy licks and satisfied purrs, leaving behind only a lingering sweetness in the air.

![image.png](attachment:61620986-6687-41f4-be31-69385d8cd487:image.png)

- CHARACTER DESCRIPTION 
**Marmalade:** A ginger cat with thick, fluffy fur. Her eyes are a warm amber, and her expression is one of quiet contentment and cunning. She is sitting upright on a wooden crate, her tail neatly curled. She wears no clothing or accessories.

        **Barnaby:** A small, scruffy terrier with brown and white fur. One ear flops over playfully. His tail wags constantly, reflecting his excited mood.  His expression is pure joy. He wears no clothing or accessories and is standing on all four paws.

![image.png](attachment:6ec9164d-8d36-427f-b6ed-d936aa380526:image.png)

- BACKGROUND DESCRIPTION 
The scene unfolds under the dappled shade of a large, ancient mango tree, its branches heavy with ripe, golden fruit. Sunlight filters through the leaves, casting a warm, inviting glow. The ground is covered in soft, mossy earth, dotted with wildflowers. A weathered wooden crate sits near the base of the tree, slightly to the left of center. To the right, a small, partially visible stone wall suggests a nearby orchard. The overall palette is warm and inviting, with shades of greens, golds, and browns dominating. The air is filled with a gentle breeze, rustling the leaves and creating a sense of calm and tranquility.

![image.png](attachment:b0ccfbb5-5970-44a8-993c-9b5f13d220d1:image.png)
