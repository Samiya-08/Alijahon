from django.urls import path

from apps.views import (AuthView, HomeListView, ProfileFormView, LogoutView, ProductListView, get_districts, \
    ChangePasswordView, WishlistView, ProductDetailView, LikeListView, OrderFormView, OrderListView, MarketListView, \
    ThreadFormView, ThreadListView, CompetitionListView, ThreedProductDetailView, ThreadStatisticDetailView,
    OperatorTemplateView,
    OperatorOrderChangeDetailView, OrderUpdateView, PaymentFormView, DiagramView)

#main
urlpatterns = [
    path('', HomeListView.as_view(), name='home'),
    path('products/<str:slug>', ProductListView.as_view(), name='product-list'),
    path('wishlist/<int:product_id>', WishlistView.as_view(), name='wishlist'),
    path('wishlist', LikeListView.as_view(), name='wish-list'),
    path('product/detail/<str:slug>', ProductDetailView.as_view(), name='product-detail'),

]
#auth
urlpatterns += [
    path("login", AuthView.as_view(), name='login'),
    path('profile', ProfileFormView.as_view(), name='profile'),
    path('logut', LogoutView.as_view(), name='logout'),
    # path('district-list', district_list_view, name= 'district-list'),
    path('get_districts', get_districts, name='get_districts'),
    path('change-password', ChangePasswordView.as_view(), name='change-password'),

]

# orders
urlpatterns += [
    path('order/form', OrderFormView.as_view(), name='order'),
    path('order/list', OrderListView.as_view(), name='order-list'),
    path('order/update/<int:pk>', OrderUpdateView.as_view(), name='order-update'),
]

# market
urlpatterns += [
    path('market/list/<str:slug>', MarketListView.as_view(), name='market-list'),
    path('competition', CompetitionListView.as_view(), name='competition'),

]

# thread
urlpatterns += [
    path('thread/form', ThreadFormView.as_view(), name='thread-form'),
    path('thread/list', ThreadListView.as_view(), name='thread-list'),
    path("thread/<int:pk>", ThreedProductDetailView.as_view(), name="threed-product"),
    path("thread/statistic", ThreadStatisticDetailView.as_view(), name="thread-statistic"),
]

#operator
urlpatterns += [
    path('operator', OperatorTemplateView.as_view(), name='operator'),
    path('operator/order-change/<int:pk>', OperatorOrderChangeDetailView.as_view(), name='order-change')
]

#payment
urlpatterns += [
    path('payment', PaymentFormView.as_view(), name='payment'),
]

#diagram
urlpatterns += [
    path('diagram/', DiagramView.as_view(), name='diagram'),
]

