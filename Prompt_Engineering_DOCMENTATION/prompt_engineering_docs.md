# Prompt Engineering Documentation

### Overview

I have used a sophisticated prompt engineering approach to generate cohesive Studio Ghibli-style stories with accompanying artwork. The process involves multiple stages of prompt refinement and specialized chains for different content types.

---

## Story Generation Prompt Structure

### Primary Story Prompt Template

The core story generation uses a structured prompt template that ensures consistency and adherence to Studio Ghibli aesthetics:

```python
prompt_template = """
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
```

### Key Components Breakdown

#### 1. Role Definition
- **Purpose**: Establishes the AI as both a "creative writer and concept artist"
- **Impact**: Creates dual expertise for both narrative and visual content generation

#### 2. Output Structure Requirements
The prompt explicitly requests three distinct outputs:
- **Short Story**: 3 paragraphs in Studio Ghibli style
- **Character Description**: Detailed visual descriptions with white background specification
- **Background Description**: Environment details without characters

#### 3. Constraint Rules
- **Inclusion Mandate**: Forces inclusion of all key objects/characters
- **Visual Specificity**: Requires appearance, size, color, and placement details
- **Tone Consistency**: Maintains "whimsical, heartfelt storytelling"

#### 4. Dynamic Variables
- `{key_objects}`: Extracted keywords from user input
- `{format_instructions}`: Pydantic schema formatting
- `{user_prompt}`: Original user request

### Key Object Extraction Logic

```python
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
```

**Strategy**: 
- Extracts all meaningful words while filtering common articles/prepositions
- Preserves order and removes duplicates
- Ensures visual consistency across all generated content

---

## Image Prompt Construction System

### Two-Stage Refinement Process

The system uses a specialized refinement chain to convert descriptive text into optimized image generation prompts.

### Image Prompt Refiner Template

```python
prompt_template = """
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
```

### Style Context Foundation

```python
def _extract_style_context() -> str:
    return (
        "Studio Ghibli art style, watercolor painting, soft pastel tones, "
        "cinematic lighting, highly detailed, masterpiece, consistent perspective, "
        "natural integration between characters and environment"
    )
```

**Design Philosophy**: 
- Establishes consistent visual identity across all images
- Balances artistic style with technical quality descriptors
- Ensures environmental harmony between elements

---

## Three Image Generation Approaches

### 1. Full Scene Image

**Construction Process**:
```python
full_scene_desc = (
    f"\nOriginal idea: \"{user_prompt}\".\n"
    f"Scene includes: {story_data.character_description.replace('on a plain white background', 'naturally integrated into the scene')}.\n"
    f"Background: {story_data.background_description}.\n"
    f"All important objects must be clearly visible: {', '.join(key_objects)}.\n"
)
```

**Key Strategies**:
- **Context Preservation**: Maintains connection to original user intent
- **Background Replacement**: Dynamically replaces "white background" with scene integration
- **Object Visibility**: Explicitly ensures all key elements are prominent
- **Narrative Cohesion**: Combines character and environment descriptions

### 2. Character-Only Image

**Construction Process**:
```python
char_prompt = refiner_chain.invoke({
    "description": f"{story_data.character_description}, isolated, white background, character study.",
    "style_context": style_context,
    "key_objects": ", ".join(key_objects)
})
```

**Design Decisions**:
- **Isolation Strategy**: Uses white background for clean character separation
- **Study Format**: Frames as "character study" for artistic focus
- **Detail Preservation**: Maintains all character-specific details from story generation

### 3. Background-Only Image

**Construction Process**:
```python
bg_prompt = refiner_chain.invoke({
    "description": f"{story_data.background_description}, no characters, environment only.",
    "style_context": style_context,
    "key_objects": ", ".join(key_objects)
})
```

**Environmental Focus**:
- **Character Exclusion**: Explicitly removes characters for pure environment
- **Object Integration**: Maintains story-relevant objects in the scene
- **Atmospheric Emphasis**: Allows full focus on lighting, mood, and setting


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

