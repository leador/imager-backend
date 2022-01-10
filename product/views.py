from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django_filters import rest_framework as df_filters
from django_redis import get_redis_connection
from rest_framework import status, exceptions
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from actions.utils import brand_remove_action
from brand.models import BrandUser

from core import settings
from other.choices import Verb
from other.models import Comment
from other.serializers import CommentSerializer
from other.utils import get_client_ip
from other.views import CharArrayFilter
from .models import Product, ProductLike, ProductRating, ProductImage
from .paginator import ProductListPaginator, ProductSearchPaginator
from .serializers import ProductSerializer, ProductCreateSerializer

r = get_redis_connection("default")


class ProductListFilter(df_filters.FilterSet):
    type = CharArrayFilter(field_name='type__slug', lookup_expr='in')

    class Meta:
        model = Product
        fields = ['type']


class ProductListAPI(APIView, ProductListPaginator):
    filter_backends = [df_filters.DjangoFilterBackend]
    filterset_class = ProductListFilter

    def get(self, request):
        fields = ['id', 'name', 'type', 'brand', 'images', 'category', 'own_category', 'slug', 'description',
                  'price', 'old_price', 'stock', 'status', 'is_sale', 'created_at']
        products = Product.objects.filter(status=True)
        for backend in list(self.filter_backends):
            products = backend().filter_queryset(self.request, products, self)
        paginated_products = self.paginate_queryset(products, self.request)
        serializer = ProductSerializer(paginated_products, many=True, fields=fields, context={'fields': fields})
        return Response({
            'success': True,
            'data': self.get_paginated_response(serializer.data)
        }, status=status.HTTP_200_OK)


class ProductCommentAPI(APIView):

    @staticmethod
    def get(request, product_slug):
        fields = ['uuid', 'user', 'text', 'parent', 'created_at', 'updated_at']
        product = get_object_or_404(Product, is_active=True, slug=product_slug)
        comments = Comment.objects.filter(used_to=product, is_active=True).order_by('-created_at')
        serializer = CommentSerializer(comments, fields=fields, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)

    def post(self, request, product_slug):
        fields = ['uuid', 'user', 'text', 'parent']
        user = self.request.user
        if not user.is_authenticated:
            raise exceptions.AuthenticationFailed({"detail": _("You must authenticate.")})
        product = get_object_or_404(Product, is_active=True, slug=product_slug)
        serializer = CommentSerializer(data=request.data, fields=fields)
        if serializer.is_valid():
            serializer.save(user=user, used_to=product)
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)


class ProductCommentDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, uuid):
        fields = ['uuid', 'user', 'text', 'parent', 'created_at', 'updated_at']
        user = self.request.user
        comment = get_object_or_404(Comment, is_active=True, user=user, uuid=uuid)
        serializer = CommentSerializer(comment, data=request.data, fields=fields)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, uuid):
        user = self.request.user
        comment = get_object_or_404(Comment, user=user, uuid=uuid)
        comment.is_active = False
        comment.save()
        return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)


class ProductRatingAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, product_slug, rating):
        user = self.request.user
        product = get_object_or_404(Product, is_active=True, slug=product_slug)
        if not isinstance(rating, int) or rating > 5 or rating < 0:
            raise exceptions.ValidationError()
        try:
            rating_model = ProductRating.objects.get(user=user, product=product)
        except ObjectDoesNotExist:
            ProductRating.objects.create(user=user, product=product, rating=rating)
            return Response({
                'success': True
            }, status=status.HTTP_201_CREATED)
        rating_model.rating = rating
        rating_model.save()
        return Response({
            'success': True
        }, status=status.HTTP_200_OK)


class ProductLikeAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, product_slug):
        user = self.request.user
        product = get_object_or_404(Product, is_active=True, slug=product_slug)
        try:
            like_model = ProductLike.objects.get(user=user, product=product)
        except ObjectDoesNotExist:
            ProductLike.objects.create(user=user, product=product)
            return Response({
                'success': True
            }, status=status.HTTP_201_CREATED)
        like_model.delete()
        return Response({
            'success': True
        }, status=status.HTTP_204_NO_CONTENT)


class ProductFilter(df_filters.FilterSet):
    min_price = df_filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = df_filters.NumberFilter(field_name="price", lookup_expr='lte')
    sort_by = df_filters.OrderingFilter(fields=(('created_at', 'newest'), 'price', ('rating', 'popularity')))
    brand__name = df_filters.CharFilter(lookup_expr='icontains')
    color = CharArrayFilter(field_name='color__name', lookup_expr='in')
    category = CharArrayFilter(field_name='category__slug', lookup_expr='in')
    own_category = df_filters.CharFilter(field_name='own_category__name', lookup_expr='iexact')
    brand = df_filters.CharFilter(field_name='brand__suffix', lookup_expr='icontains')
    name = df_filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Product
        fields = ['is_sale', 'sort_by', 'rating', 'own_category', 'color', 'name', 'brand', 'min_price', 'max_price',
                  'created_at', 'category']


class ProductSearchListAPI(APIView, ProductSearchPaginator):
    filterset_class = ProductFilter
    filter_backends = [df_filters.DjangoFilterBackend]

    def get(self, request):
        fields = ['brand', 'rating', 'type', 'category', 'name', 'slug', 'price', 'color',
                  'old_price', 'is_sale', 'images', 'status', 'own_category']
        user = self.request.user
        for key in request.query_params.keys():
            if key == 'p':
                continue
            elif key not in ProductFilter.Meta.fields:
                raise exceptions.NotFound()
        products = Product.objects.filter(is_active=True, status=True, brand__is_active=True, brand__status=True)
        for backend in list(self.filter_backends):
            products = backend().filter_queryset(self.request, products, self)
        paginated_products = self.paginate_queryset(list(dict.fromkeys(products)), self.request)
        serializer = ProductSerializer(paginated_products, many=True, fields=fields)
        return Response({
            'success': True,
            'data': self.get_paginated_response(serializer.data)
        }, status=status.HTTP_200_OK)


class FollowedBrandProductsAPI(APIView, ProductListPaginator):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        fields = ['brand', 'rating', 'type', 'category', 'name', 'slug', 'price', 'color',
                  'old_price', 'is_sale', 'images', 'own_category', 'status']
        user = self.request.user
        followed_brand_ids = user.followings_brand.values_list('id', flat=True)
        followed_products = Product.objects.filter(is_active=True, status=True, stock__gt=0,
                                                   brand__pk__in=followed_brand_ids)
        paginated_products = self.paginate_queryset(followed_products, self.request)
        serializer = ProductSerializer(paginated_products, many=True, fields=fields, context={'fields': fields})
        return Response({
            'success': True,
            'data': self.get_paginated_response(serializer.data)
        }, status=status.HTTP_200_OK)


class ProductMemberListAPI(APIView, ProductListPaginator):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        fields = ['id', 'name', 'type', 'brand', 'images', 'category', 'own_category', 'slug', 'description',
                  'price', 'old_price', 'stock', 'status', 'is_sale', 'created_at']
        user = self.request.user
        try:
            brand = user.brand_user.brand
        except ObjectDoesNotExist:
            raise exceptions.NotFound()
        products = Product.objects.filter(is_active=True, brand=brand, brand__is_active=True)
        paginated_products = self.paginate_queryset(products, self.request)
        serializer = ProductSerializer(paginated_products, many=True, fields=fields)
        return Response({
            'success': True,
            'data': self.get_paginated_response(serializer.data)
        }, status=status.HTTP_200_OK)

    def post(self, request):
        fields = ['name', 'category', 'type', 'own_category', 'slug', 'tags', 'images',
                  'vendor_code', 'sizes', 'origin', 'color', 'barcode', 'discount', 'price',
                  'old_price', 'stock', 'description', 'is_sale']
        user = self.request.user
        try:
            brand = user.brand_user.brand
        except ObjectDoesNotExist:
            raise exceptions.NotFound()
        if brand.is_active:
            try:
                images_list = request.data['images']
            except:
                raise exceptions.ValidationError({'errors': {'images': _('Include images')}})
            try:
                type_ = request.data['type']
            except:
                raise exceptions.ValidationError({'errors': {'type': _('Choose one of types')}})
            try:
                category = request.data['category']
            except:
                raise exceptions.ValidationError({'errors': {'category': _('Choose one of categories')}})
            # Other nested data
            category = request.data.pop('category', None)
            own_category = request.data.pop('own_category', None)
            tags = request.data.pop('tags', None)
            type_ = request.data.pop('type', None)
            color = request.data.pop('color', None)
            sizes = request.data.pop('sizes', None)
            images = request.FILES.getlist('images')
            serializer = ProductCreateSerializer(data=request.data, fields=fields)
            if serializer.is_valid():
                if len(images) > settings.MAXIMUM_PRODUCT_IMAGES:
                    raise exceptions.ValidationError(f"Maximum number of images for each product is"
                                                     f" {settings.MAXIMUM_PRODUCT_IMAGES}")
                status_ = True if brand.verified else False
                product = serializer.save(user=user.brand_user,
                                          category=category,
                                          tags=tags,
                                          status=status_,
                                          type=type_,
                                          color=color,
                                          sizes=sizes,
                                          brand=brand,
                                          own_category=own_category)
                for image in images:
                    ProductImage.objects.create(product=product, image=image)
                return Response({
                    'success': True,
                    'data': serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        raise exceptions.NotFound()


class ProductMemberDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, product_slug):
        fields = ['brand', 'name', 'slug', 'price', 'own_category', 'category', 'type', 'images',
                  'tags', 'vendor_code', 'sizes', 'origin', 'color', 'barcode', 'discount',
                  'old_price', 'stock', 'description', 'is_sale', 'created_at', 'product_views',
                  'like_count', 'rating_count']
        user = self.request.user
        try:
            brand = user.brand_user.brand
            product = get_object_or_404(Product, is_active=True, brand=brand, brand__is_active=True, slug=product_slug)
            serializer = ProductSerializer(product, fields=fields, context={'fields': fields})
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            raise exceptions.NotFound(e)

    def put(self, request, product_slug):
        fields = ['name', 'price', 'own_category', 'category', 'type',
                  'tags', 'vendor_code', 'sizes', 'origin', 'color', 'barcode', 'discount',
                  'old_price', 'stock', 'description', 'is_sale']
        user = self.request.user
        try:
            brand = user.brand_user.brand
            product = get_object_or_404(Product, is_active=True, brand=brand, brand__is_active=True, slug=product_slug)
            manager = True if user.brand_user.is_manager else False
            seller = True if product.user == user.brand_user else False
        except BrandUser.DoesNotExist:
            raise exceptions.NotFound()
        if manager or seller:
            if seller and not brand.status:
                raise exceptions.PermissionDenied()
            print('BEFORE', request.data)
            # remember old state
            _mutable = request.data._mutable
            # set to mutable
            request.data._mutable = True
            # Other nested data
            category = request.data.pop('category', None)
            own_category = request.data.pop('own_category', None)
            tags = request.data.pop('tags', None)
            type_ = request.data.pop('type', None)
            color = request.data.pop('color', None)
            sizes = request.data.pop('sizes', None)
            # set mutable flag back
            request.data._mutable = _mutable
            print('AFTER', request.data)
            serializer = ProductSerializer(product, data=request.data, fields=fields, context={'fields': fields})
            if serializer.is_valid():
                serializer.save(category=category,
                                own_category=own_category,
                                tags=tags,
                                type=type_,
                                color=color,
                                sizes=sizes)
                return Response({
                    'success': True,
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        raise exceptions.NotFound()

    def delete(self, request, product_slug):
        user = self.request.user
        try:
            brand = user.brand_user.brand
            product = get_object_or_404(Product, is_active=True, brand=brand, brand__is_active=True, slug=product_slug)
            manager = True if user.brand_user.is_manager else False
            seller = True if product.user == user.brand_user else False
        except BrandUser.DoesNotExist:
            raise exceptions.NotFound()
        if manager or seller:
            if seller and not brand.status:
                raise exceptions.PermissionDenied()
            brand_remove_action(brand, Verb.PRODUCT, product, action='delete')
            product.delete()
            return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)
        raise exceptions.NotFound()


class ProductDetailAPI(APIView):

    def get(self, request, product_slug):
        user = self.request.user
        fields = ['id', 'brand', 'name', 'slug', 'price', 'own_category', 'category', 'type',
                  'tags', 'vendor_code', 'sizes', 'origin', 'color', 'barcode', 'discount', 'product_views',
                  'old_price', 'stock', 'description', 'is_sale', 'created_at',
                  'like_count', 'rating_count', 'images']
        product = get_object_or_404(Product, is_active=True, brand__is_active=True, slug=product_slug)
        serializer = ProductSerializer(product, fields=fields, context={'fields': fields})
        ip = get_client_ip(request)
        r.zincrby(f"product:views:{product.pk}", 1, ip)
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
