from django.contrib.auth import get_user_model
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum, F
from django.db.utils import IntegrityError
from django.http import JsonResponse
from django.views.generic import TemplateView
from requests import get
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from yaml import load, Loader

from backend.models import Category, Shop, ProductInfo, Order, OrderGood, Product, Parameter, ProductParameter, Contact
from backend.permissions import IsAuthorOrReadOnly
from backend.serializers import UserSerializer, CategorySerializer, ShopSerializer, ProductInfoSerializer, \
    OrderSerializer, OrderGoodSerializer, ContactSerializer


class HomeView(TemplateView):
    template_name = 'home.html'


class UserViewSet(ModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer


class PartnerUpdateView(APIView):

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.type == 'shop':
                url = request.data.get('url')
                if url:
                    validate_url = URLValidator()
                    try:
                        validate_url(url)
                    except ValidationError as er:
                        return JsonResponse({'Status': False, 'Error': str(er)})
                    else:
                        stream = get(url).content
                        data = load(stream=stream, Loader=Loader)
                        shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)
                        for category in data['categories']:
                            category_obj, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                            category_obj.shops.add(shop.id)
                            category_obj.save()
                        ProductInfo.objects.filter(shop_id=shop.id).delete()
                        for good in data['goods']:
                            product, _ = Product.objects.get_or_create(name=good['name'], category_id=good['category'])
                            product_info = ProductInfo.objects.create(
                                product_id=product.id,
                                external_id=good['id'],
                                model=good['model'],
                                price=good['price'],
                                price_rcc=good['price_rrc'],
                                quantity=good['quantity'],
                                shop_id=shop.id
                            )
                            for name, value in good['parameters'].items():
                                parameter_obj, _ = Parameter.objects.get_or_create(name=name)
                                ProductParameter.objects.create(
                                    product_info_id=product_info.id,
                                    parameter_id=parameter_obj.id,
                                    value=value
                                )
                        return JsonResponse({'Status': True})
                else:
                    return JsonResponse({'Status': False, 'Error': 'You have not authenticated'}, status=403)
            else:
                JsonResponse({'Status': False, 'Error': 'Access denied'})
        else:
            return JsonResponse({'Status': False, 'Errors': 'You have not authenticated'})


class ContactView(APIView):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            contact = Contact.objects.filter(user_id=request.user.id)
            serializer = ContactSerializer(contact, many=True)
            return Response(serializer.data)
        else:
            return JsonResponse({'Status': False, 'Errors': 'You have not authenticated'})

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if {'city', 'street', 'phone'}.issubset(request.data):
                request.data._mutable = True
                request.data.update({'user': request.user.id})
                serializer = ContactSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return JsonResponse({'Status': True})
                else:
                    JsonResponse({'Status': False, 'Error': 'Invalid request'})
            else:
                return JsonResponse({'Status': False, 'Errors': "You didn't specify all the arguments"})
        else:
            return JsonResponse({'Status': False, 'Errors': 'You have not authenticated'})

    def delete(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            goods = request.data.get('goods')
            if goods:
                goods_list = goods.split(',')
                query = Q()
                objects_deleted = False
                for contact_id in goods_list:
                    if contact_id.isdigit():
                        query = query | Q(user_id=request.user.id, id=contact_id)
                        objects_deleted = True
                if objects_deleted:
                    counter = Contact.objects.filter(query).delete()[0]
                    return JsonResponse({'Status': True, 'Deleted objects': counter})
            else:
                return JsonResponse({'Status': False, 'Error': "You didn't specify all the arguments"})
        else:
            return JsonResponse({'Status': False, 'Errors': 'You have not authenticated'})

    def put(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if 'id' in request.data:
                id_ = request.data['id']
                if id_.isdigit():
                    contact = Contact.objects.filter(id=id_, user_id=request.user.id).first()
                    if contact:
                        serializer = ContactSerializer(contact, data=request.data, partial=True)
                        if serializer.is_valid():
                            serializer.save()
                            return JsonResponse({'Status': True})
                        else:
                            JsonResponse({'Status': False, 'Error': 'Invalid request'})
                    else:
                        return JsonResponse({'Status': False, 'Error': 'There is no such contact'})
            else:
                return JsonResponse({'Status': False, 'Error': "You didn't specify all the arguments"})
        else:
            return JsonResponse({'Status': False, 'Errors': 'You have not authenticated'})


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    ordering = ('name', )

    def get_permissions(self):
        if self.action == 'list':
            permission_classes = [IsAuthenticatedOrReadOnly]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


class ShopViewSet(ModelViewSet):
    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopSerializer
    ordering = ('name', )

    def get_permissions(self):
        if self.action == 'list':
            permission_classes = [IsAuthenticatedOrReadOnly]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


class OrderView(APIView):
    permission_classes = (IsAuthorOrReadOnly, )

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            order = Order.objects.filter(user_id=request.user.id).exclude(state='cart').\
                prefetch_related('ordered_goods__product_info__product__category',
                                 'ordered_goods__product_info__product_parameters__parameter')\
                .select_related('contact').annotate(
                total_price=Sum(F('ordered_goods__quantity') * F('ordered_goods__product_info__price'))).distinct()
            serializer = OrderSerializer(order, many=True)
            return Response(serializer.data)
        else:
            return JsonResponse({'Status': False, 'Errors': 'You have not authenticated'})

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if {'id', 'contact'}.issubset(request.data):
                id_ = request.data['id']
                if id_.isdigit():
                    try:
                        is_done = Order.objects.filter(
                            user_id=request.user.id,
                            id=id_).update(contact_id=request.data['contact'], state='new')
                        print(is_done)
                    except IntegrityError as er:
                        return JsonResponse({'Status': False, 'Error': str(er)})
                    else:
                        return JsonResponse({'Status': True})
                else:
                    return JsonResponse({'Status': False, 'Error': 'Invalid request'})
            else:
                return JsonResponse({'Status': False, 'Error': "You didn't specify all the arguments"})
        else:
            return JsonResponse({'Status': False, 'Errors': 'You have not authenticated'})


class ProductInfoView(APIView):

    def get(self, request, *args, **kwargs):
        query = Q(shop__state=True)
        shop_id = request.query_params.get('shop_id')
        category_id = request.query_params.get('category_id')
        if shop_id:
            query = query & Q(shop_id=shop_id)
        if category_id:
            query = query & Q(product__category_id=category_id)
        queryset = ProductInfo.objects.filter(query).select_related('shop', 'product__category').prefetch_related(
            'product_parameters_parameter').distinct()
        serializer = ProductInfoSerializer(queryset, many=True)
        return Response(serializer.data)


class CartView(APIView):

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            cart = Order.objects.filter(user_id=request.user.id, state='cart').\
                prefetch_related('ordered_goods__product_info_product__category',
                                 'ordered_goods__product_info__product_parameters__parameter').\
                annotate(
                total_price=Sum(F('ordered_goods__quantity') * F('ordered_goods__product_info__price'))).distinct()
            serializer = OrderSerializer(cart, many=True)
            return Response(serializer.data)
        else:
            return JsonResponse({'Status': False, 'Error': 'You have not authenticated'}, status=403)

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            goods = request.data.get('goods')
            if goods:
                try:
                    goods_dict = goods
                except ValueError:
                    JsonResponse({'Status': False, 'Error': 'Invalid request'})
                else:
                    cart, _ = Order.objects.get_or_create(user_id=request.user.id, state='cart')
                    counter = 0
                    for good in goods_dict:
                        good.update({'order': cart.id})
                        serializer = OrderGoodSerializer(data=good)
                        if serializer.is_valid():
                            try:
                                serializer.save()
                            except IntegrityError as er:
                                return JsonResponse({'Status': False, 'Error': str(er)})
                            else:
                                counter += 1
                        else:
                            JsonResponse({'Status': False, 'Error': serializer.errors})
                    return JsonResponse({'Status': True, 'Objects created': counter})
            else:
                return JsonResponse({'Status': False, 'Error': "You didn't specify all the arguments"})
        else:
            return JsonResponse({'Status': False, 'Error': 'You have not authenticated'}, status=403)

    def delete(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            goods = request.data.get('goods')
            if goods:
                goods_list = goods.split(',')
                cart, _ = Order.objects.get_or_create(user_id=request.user.id, state='cart')
                query = Q()
                objects_deleted = False
                for good_id in goods_list:
                    if good_id.isdigit():
                        query = query | Q(order_id=cart.id, id=good_id)
                        objects_deleted =True
                    if objects_deleted:
                        counter = OrderGood.objects.filter(query).delete()[0]
                        return JsonResponse({'Status': True, 'Deleted objects': counter})
            else:
                return JsonResponse({'Status': False, 'Error': "You didn't specify all the arguments"})
        else:
            return JsonResponse({'Status': False, 'Error': 'You have not authenticated'}, status=403)

    def put(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            goods = request.data.get('goods')
            if goods:
                try:
                    goods_dict = goods
                except ValueError:
                    JsonResponse({'Status': False, 'Error': 'Invalid request'})
                else:
                    cart, _ = Order.objects.get_or_create(user_id=request.user.id, state='cart')
                    counter = 0
                    for good in goods_dict:
                        id = good['id']
                        quantity = good['quantity']
                        if type(id) == int and type(quantity) == int:
                            new_good = OrderGood.objects.filter(order_id=cart.id, id=id).update(quantity=quantity)
                            counter += new_good
                    return JsonResponse({'Status': True, 'Updated objects': counter})
            else:
                return JsonResponse({'Status': False, 'Error': "You didn't specify all the arguments"})
        else:
            return JsonResponse({'Status': False, 'Error': 'You have not authenticated'}, status=403)


class PartnerStateViewSet(ModelViewSet):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer


class PartnerOrderView(APIView):

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.type == 'shop':
                order = Order.objects.filter(
                    ordered_goods__product_info__shop__user_id=request.user.id).exclude(
                    state='cart').prefetch_related(
                    'ordered_goods__product_info_product_category',
                    'ordered_goods__product_info_product_parameters__parameter').select_related('contact').anotate(
                    total_price=Sum(F('ordered_goods__quantity') * F('ordered_goods__product_info__price'))).distinct()
                serializer = OrderSerializer(order, many=True)
                return Response(serializer.data)
            else:
                return JsonResponse({'Status': False, 'Error': 'Access denied'})
        else:
            return JsonResponse({'Status': False, 'Error': 'You have not authenticated'}, status=403)
