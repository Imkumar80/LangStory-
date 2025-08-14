import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .services.story_service import generate_story_and_images, GenerationError


logger = logging.getLogger('story')


@api_view(['POST'])
def generate_api(request):
    prompt = ''
    try:
        prompt = (request.data.get('prompt') or '').strip()
    except Exception:
        prompt = ''

    if not prompt:
        return Response({'error': 'Field "prompt" is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        result = generate_story_and_images(prompt)
        return Response(result, status=status.HTTP_200_OK)
    except GenerationError as e:
        logger.warning('Generation error: %s', e)
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        logger.exception('Unexpected error in API generation')
        return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


