from rest_framework.routers import DefaultRouter
from django.urls import path

from backend.views import UserViewSet, CategoryViewSet, ShopViewSet, PartnerStateViewSet, PartnerUpdateView, \
    ContactView, OrderView, ProductInfoView, CartView, PartnerOrderView

router = DefaultRouter()

router.register('users/', UserViewSet, basename='users')
router.register('categories/', CategoryViewSet, basename='categories')
router.register('shops/', ShopViewSet, basename='shops')
router.register('partner/state/', PartnerStateViewSet, basename='partner-state')


urlpatterns = [
    path('partner/update/', PartnerUpdateView.as_view(), name='partner-update'),
    path('users/contact/', ContactView.as_view(), name='user-contact'),
    path('order/', OrderView.as_view(), name='order'),
    path('products/', ProductInfoView.as_view(), name='products'),
    path('cart/', CartView.as_view(), name='cart'),
    path('partner/orders/', PartnerOrderView.as_view(), name='partner-order'),
] + router.urls
