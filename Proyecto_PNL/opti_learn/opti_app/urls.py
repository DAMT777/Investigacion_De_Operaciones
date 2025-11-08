from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import index, ParseProblemAPIView, ProblemViewSet, SolutionViewSet, method_view


router = DefaultRouter()
router.register(r'problems', ProblemViewSet, basename='problem')
router.register(r'solutions', SolutionViewSet, basename='solution')


urlpatterns = [
    path('', index, name='index'),
    path('methods/<str:method_key>', method_view, name='method'),
    path('api/problems/parse', ParseProblemAPIView.as_view(), name='problems-parse'),
    path('api/', include(router.urls)),
]
