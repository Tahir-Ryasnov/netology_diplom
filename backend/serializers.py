from django.contrib.auth import get_user_model
from rest_framework import serializers

from backend.models import Contact, Category, Shop, ProductParameter, Product, ProductInfo, OrderGood, Order


class ContactSerializer(serializers.ModelSerializer):

    class Meta:
        model = Contact
        fields = ('id', 'city', 'street', 'house', 'structure', 'building', 'apartment', 'user', 'phone')
        read_only_fields = ('id', )
        extra_kwargs = {'user': {'write_only': True}}


class UserSerializer(serializers.ModelSerializer):
    contacts = ContactSerializer(read_only=True, many=True)

    class Meta:
        model = get_user_model()
        fields = (
            'id', 'username', 'first_name', 'last_name', 'email', 'company', 'position', 'is_active', 'type', 'contacts'
        )
        read_only_fields = ('id', )


class CategorySerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

    class Meta:
        model = Category
        fields = ('id', 'name', )
        read_only_fields = ('id', )


class ShopSerializer(serializers.ModelSerializer):

    class Meta:
        model = Shop
        fields = ('id', 'name', 'state')
        read_only_fields = ('id', )


class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ('value', 'parameter')


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ('name', 'category')


class ProductInfoSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    parameters = ProductParameterSerializer(read_only=True, many=True)

    class Meta:
        model = ProductInfo
        fields = ('id', 'model', 'product', 'shop', 'quantity', 'price', 'price_rcc', 'external_id', 'parameters')
        read_only_fields = ('id', )


class OrderGoodSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrderGood
        fields = ('id', 'product_info', 'quantity', 'order')
        read_only_fields = ('id', )
        extra_kwargs = {'order': {'write_only': True}}


class OrderGoodCreateSerializer(OrderGoodSerializer):
    product_info = ProductInfoSerializer(read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    goods = OrderGoodCreateSerializer(read_only=True, many=True)
    total_price = serializers.IntegerField()
    contact = ContactSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'goods', 'total_price', 'date', 'state', 'contact')
        read_only_fields = ('id', )
