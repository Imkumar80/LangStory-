import logging
from datetime import datetime # --> ADDED: Import datetime module
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.conf import settings
from .services.story_service import generate_story_and_images, GenerationError


logger = logging.getLogger('story')


def index(request):
    return render(request, 'story/index.html', {})


@require_http_methods(["POST"]) 
def generate_story(request):
    user_prompt = request.POST.get('prompt', '').strip()
    if not user_prompt:
        return render(request, 'story/index.html', {
            'error': 'Please enter a prompt.',
        })

    try:
        # Your service function returns the result dictionary as before
        result = generate_story_and_images(user_prompt)

        # --> ADDED: Create a unique timestamp and add it to the result dictionary
        result['cache_buster'] = int(datetime.now().timestamp())
        
        # The modified 'result' dictionary is now passed to the template
        return render(request, 'story/result.html', result)
        
    except GenerationError as e:
        logger.exception('Generation failed')
        return render(request, 'story/index.html', {
            'error': str(e),
        })