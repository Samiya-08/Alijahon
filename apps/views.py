from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.hashers import check_password

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count, F, Sum
from django.http import JsonResponse
# from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, FormView, ListView, DetailView, UpdateView

from apps.forms import AuthForm, ProfileForm, ChangePasswordForm, OrderForm, ThreadForm, OrderModelForm, \
    PaymentModelForm
from apps.models import User, District, Region, Category, Product, Wishlist, AdminSetting, Order, Thread


class AuthView(FormView):
    form_class = AuthForm
    template_name = 'apps/auth/auth.html'
    success_url = reverse_lazy('profile')

    # def get_context_data(self, **kwargs):
    #     data = super().get_context_data(**kwargs)
    #     data['regions'] = Region.objects.all()
    #     return data

    def form_valid(self, form):
        data = form.cleaned_data
        phone_number = data.get("phone_number")
        password = form.data.get("password")
        hash_password = data.get("password")
        query_set = User.objects.filter(phone_number=phone_number)
        if query_set.exists():
            user = query_set.first()
            if user.check_password(password):
                login(self.request, user)
            else:
                messages.error(self.request, "Parol xato !")
                return redirect('login')
        else:
            user = User.objects.create(password=hash_password, phone_number=phone_number)
            login(self.request, user)

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "\n".join([error[0] for error in form.errors.values()]))
        return super().form_invalid(form)


class HomeListView(ListView):
    queryset = Category.objects.all()
    template_name = 'apps/home.html'
    context_object_name = 'categories'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['products'] = Product.objects.all()
        if self.request.user.is_authenticated:
            data['liked_products_id'] = Wishlist.objects.filter(user_id=self.request.user).values_list("product_id",
                                                                                                   flat=True)
        return data


class ProfileFormView(LoginRequiredMixin, FormView):
    form_class = ProfileForm
    template_name = 'apps/auth/profile.html'
    success_url = reverse_lazy('profile')
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['regions'] = Region.objects.all()
        return data

    def form_valid(self, form):
        form.update(self.request.user)
        return super().form_valid(form)

    def form_invalid(self, form):
        pass


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')


def get_districts(request):
    region_id = request.GET.get('region_id')
    districts = District.objects.filter(region_id=region_id).values('id', 'name')
    return JsonResponse(list(districts), safe=False)


class ChangePasswordView(FormView):
    form_class = ChangePasswordForm
    template_name = 'apps/auth/profile.html'
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        session_password = self.request.user.password
        old_password = form.cleaned_data.get('old')

        # Check if old password matches the current password
        if not check_password(old_password, session_password):
            messages.error(self.request, 'Old password incorrect.')
            return self.form_invalid(form)

        new_password = form.cleaned_data.get('new')
        self.request.user.set_password(new_password)
        self.request.user.save()

        update_session_auth_hash(self.request, self.request.user)

        messages.success(self.request, 'Your password has been changed successfully.')


        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)

class ProductListView(ListView):
    queryset = Product.objects.all()
    template_name = 'apps/menus/product-list.html'
    context_object_name = 'products'

    def get_context_data(self, *, object_list=None, **kwargs):
        slug = self.kwargs.get('slug')
        category = Category.objects.filter(slug=slug).first()
        data = super().get_context_data(object_list=object_list, **kwargs)
        products = Product.objects.all()
        if slug != 'all':
            products = products.filter(category=category)
        # ----------- SEARCH ---------------
        query = self.request.GET.get("query")
        if query:
            products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

        data['products'] = products
        # ------------- SEARCH-------------
        data['categories'] = Category.objects.all()
        if self.request.user.is_authenticated:
            data['liked_products_id'] = Wishlist.objects.filter(user_id=self.request.user).values_list("product_id",
                                                                                                   flat=True)
        data['session_category'] = category
        return data

class WishlistView(LoginRequiredMixin, View):
    login_url = reverse_lazy('login')
    def get(self, request, product_id):
        liked = True
        like = Wishlist.objects.filter(product_id=product_id, user=self.request.user)
        if like.exists():
            like.delete()
            liked = False
        else:
            Wishlist.objects.create(product_id=product_id, user=self.request.user)

        return JsonResponse({"liked": liked})

class ProductDetailView(DetailView):
    queryset = Product.objects.all()
    template_name = 'apps/order/product-detail.html'
    slug_url_kwarg = 'slug'
    context_object_name = 'product'

class LikeListView(ListView):
    queryset = Wishlist.objects.all()
    template_name = 'apps/menus/wishlist.html'
    context_object_name = 'products'

    def get_context_data(self, *, object_list=None, **kwargs):
        data =  super().get_context_data(object_list=object_list, **kwargs)
        data['products'] = Product.objects.filter(wishlist__user=self.request.user)
        if self.request.user.is_authenticated:
            data['liked_products_id'] = Wishlist.objects.filter(user_id=self.request.user).values_list("product_id",
                                                                                                   flat=True)
        return data

class OrderFormView(FormView):
    form_class = OrderForm
    template_name = 'apps/order/product-detail.html'
    success_url = reverse_lazy('order')

    def form_valid(self, form):
        form.cleaned_data['owner_id'] = self.request.user.id
        deliver_price = AdminSetting.objects.first().deliver_price
        order = form.save(deliver_price)
        return render(self.request, 'apps/order/success.html', context={"order": order, "deliver_price": deliver_price})

    def form_invalid(self, form):
        pass

class ProductSearchView(View):
    def post(self, request):
        query = request.GET.get('query')
        products = Product.objects.filter(Q(name__icontains=query) |Q(description__icontains = query))
        return render(request, '')

class OrderListView(ListView):
    login_url = reverse_lazy('login')
    queryset = Order.objects.all()
    template_name = 'apps/order/order-list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        return Order.objects.filter(owner_id=self.request.user.id)

    # def get_context_data(self, *, object_list=None, **kwargs):
    #     data = super().get_context_data(object_list=object_list, **kwargs)
    #     data['orders'] = data.get('orders').filter(owner=self.request.user)
    #     return data

class MarketListView(LoginRequiredMixin, ListView):
    queryset = Product.objects.all()
    template_name = 'apps/thread/market.html'
    context_object_name = 'products'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        products = Product.objects.all()
        slug = self.kwargs.get('slug')
        data = super().get_context_data(**kwargs)
        data['categories'] = Category.objects.all()
        query  = self.request.GET.get('query')
        if query:
            products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
        if slug != 'all':
            products = products.filter(category__slug=slug)
        if slug == 'top':
            products = products.annotate(order_count=Count(F('orders'))).order_by('order_count')
        data['products'] = products
        return data

class ThreadFormView(FormView):
    form_class = ThreadForm
    template_name = 'apps/thread/market.html'
    success_url = reverse_lazy('thread-list')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['products'] = Product.objects.all()
        return data

    def form_valid(self, form):
        pass
        thread = form.save(commit=False)
        thread.user = self.request.user
        thread.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        pass
        for message in form.errors.values():
            messages.error(self.request, message)
        return super().form_invalid(form)

class ThreadListView(ListView):
    queryset = Thread.objects.all()
    template_name = 'apps/thread/thread-list.html'
    context_object_name = 'threads'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['threads'] = data.get('threads').filter(user=self.request.user).order_by('-created_at')
        return data

class ThreedProductDetailView(DetailView):
    queryset = Thread.objects.all()
    template_name = "apps/order/product-detail.html"
    context_object_name = "thread"

    def get_context_data(self, **kwargs):
        pass
        data =  super().get_context_data(**kwargs)
        thread = data.get('thread')
        data["product"] = thread.product
        thread.visit_count += 1
        thread.save()
        return data

class ThreadStatisticDetailView(TemplateView):
    template_name = "apps/thread/thread-statistic.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        statistics = Thread.objects.filter(user=self.request.user).annotate(
            new_count=Count('orders', filter=Q(orders__status = Order.StatusType.NEW)),
            ready_to_order_count=Count('orders', filter=Q(orders__status =Order.StatusType.READY_TO_ORDER)),
            delivering_count=Count('orders', filter=Q(orders__status =Order.StatusType.DELIVERING)),
            delivered_count=Count('orders', filter=Q(orders__status =Order.StatusType.DELIVERED)),
            not_pick_up_count=Count('orders', filter=Q(orders__status =Order.StatusType.NOT_PICK_UP)),
            canceled_count=Count('orders', filter=Q(orders__status =Order.StatusType.CANCELED)),
            archived_count=Count('orders', filter=Q(orders__status =Order.StatusType.ARCHIVED))
        ).only('name', 'product__name', 'visit_count')

        tmp = statistics.aggregate(
            all_visit_count=Sum('visit_count'),
            all_ready_to_order_count=Sum('ready_to_order_count'),
            all_delivering_count=Sum('delivering_count'),
            all_delivered_count=Sum('delivered_count'),
            all_not_pick_up_count=Sum('not_pick_up_count'),
            all_canceled_count=Sum('canceled_count'),
            all_archived_count=Sum('archived_count'),
        )
        data['statistics'] = statistics
        data['thread_count'] = statistics.count()
        data.update(tmp)
        return data

class CompetitionListView(ListView):
    queryset = User.objects.all()
    template_name = 'apps/menus/competition.html'
    context_object_name = 'users'

    def get_context_data(self, **kwargs):
        data =  super().get_context_data(**kwargs)
        data['site'] = AdminSetting.objects.first()
        return data

    def get_queryset(self):
        query = super().get_queryset()
        query = query.annotate(order_count=Count('thread__orders', filter=Q(thread__orders__status = Order.StatusType.COMPLETED))).only('first_name')
        return query

class OperatorTemplateView(TemplateView):
    template_name = 'apps/operator/operator-page.html'

    def post(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render(request, 'apps/operator/operator-page.html', context)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        status = self.request.GET.get('status')
        category_id = self.request.POST.get('category_id')
        district_id = self.request.POST.get('district_id')
        data['status'] = Order.StatusType.values
        data['regions'] = Region.objects.all()

        data['categories'] = Category.objects.all()
        orders = Order.objects.filter(status=Order.StatusType.NEW)
        if status:
            orders = Order.objects.filter(status=status)
        if category_id:
            orders = orders.filter(product__category_id=category_id)
        if district_id:
            orders = orders.filter(district_id=district_id)
        data['orders'] = orders
        return data

class OperatorOrderChangeDetailView(DetailView):
    queryset = Order.objects.all()
    template_name = 'apps/operator/order-change.html'
    pk_url_kwarg = 'pk'
    context_object_name = 'order'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['regions'] = Region.objects.all()
        return data

class OrderUpdateView(UpdateView):
    queryset = Order.objects.all()
    form_class = OrderModelForm
    template_name = 'apps/operator/order-change.html'
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('operator')


# class PaymentFormView(FormView):
#     queryset = Order.objects.all()
#     template_name = 'apps/menus/payment.html'
#     success_url = reverse_lazy('')

class DiagramView(TemplateView):
    template_name = 'apps/menus/diagram.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['population_data'] = {
            'labels': [
                'Andijon', 'Buxoro', 'Farg‘ona', 'Jizzax', 'Xorazm',
                'Namangan', 'Navoiy', 'Qashqadaryo', 'Samarqand',
                'Sirdaryo', 'Surxondaryo', 'Toshkent vil.', 'Qoraqalpog‘iston'
            ],
            'values': [
                3311, 1976, 3896, 1443, 1948,
                2955, 1058, 3408, 4031,
                894, 2829, 2976, 1997
            ],
            'background_colors': [
                '#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#FF99CC',
                '#99CCFF', '#CC99FF', '#FFCC66', '#66CCCC', '#FF9966',
                '#99FFCC', '#CC66CC', '#66FF99'
            ],
            'border_colors': [
                '#FF6666', '#3399FF', '#66CC66', '#FF9966', '#FF66CC',
                '#6699FF', '#9966FF', '#FF9933', '#339999', '#FF6633',
                '#66CC99', '#993399', '#33CC66'
            ]
        }
        return data

class PaymentFormView(FormView):
    form_class = PaymentModelForm
    success_url = reverse_lazy('payment')
    template_name = 'apps/menus/payment.html'

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['payments'] = self.request.user.payments.all()
        return data

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        if amount > self.request.user.balance:
            form.add_error('amount', "Mablag' yetarli emas")
            return self.form_invalid(form)
        user = self.request.user
        user.balance -= form.cleaned_data.get('amount')
        user.save()
        form = form.save(commit = False)
        form.user = self.request.user
        form.save()

        return super().form_valid(form)

    def form_invalid(self, form):
        for error in form.errors.values():
            messages.error(self.request, error)
            return super().form_invalid(form)




