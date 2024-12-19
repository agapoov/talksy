# from rest_framework import status
# from rest_framework.views import APIView
# from rest_framework.response import Response
# import webso
#
# class TestWebSocketConnection(APIView):
#     def get(self, request):
#         try:
#             websocket = WebSocketClient("ws://example.com/socket")
#             websocket.connect()
#             return Response({"message": "WebSocket connection successful"}, status=status.HTTP_200_OK)
#         except Exception as e:
#             # В случае ошибки
#             return Response({"message": f"WebSocket connection failed: {str(e)}"},
#                             status=status.HTTP_500_INTERNAL_SERVER_ERROR)
