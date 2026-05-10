from rest_framework import renderers
import json

# class UserRenderer(renderers.JSONRenderer):
#     charset = 'utf-8'

#     def render(self, data, accepted_media_type=None, renderer_context=None):
#         response = ''
#         if 'ErrorDetail' in str(data):
#             response = json.dumps({'errors': data})
#         else:
#             response = json.dumps(data)

#         return response

from rest_framework.renderers import JSONRenderer
import json

class UserRenderer(JSONRenderer):
    charset = 'utf-8'

    def render(self, data, accepted_media_type=None, renderer_context=None):

        response = renderer_context.get('response')

        if response and response.status_code >= 400:
            return json.dumps({
                'errors': data
            })

        return json.dumps(data)