import re

from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.forms import CharField, IntegerField
from django.forms.forms import Form
from django.forms.models import ModelForm
from apps.models import User, Order, Thread, Product, AdminSetting, Payment


class AuthForm(Form):
    phone_number = CharField(max_length=20)
    password = CharField(max_length=255)

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number")
        return "+" + re.sub('\D', "", phone_number)

    def clean_password(self):
        password = self.cleaned_data.get("password")
        return make_password(password)

class LoginForm(Form):
    first_name = CharField(required=False)
    last_name = CharField(required=False)
    district_id = CharField(required=False)
    address = CharField(required=False)
    telegram_id = IntegerField(required=False)

class ProfileForm(LoginRequiredMixin, Form):
    first_name = CharField(required=False)
    last_name = CharField(required=False)
    district_id = CharField(required=False)
    address = CharField(required=False)
    telegram_id = IntegerField(required=False)
    about = CharField(required=False)

    def update(self, user):
        data = self.cleaned_data
        User.objects.filter(pk=user.pk).update(**data)

class ChangePasswordForm(Form):
    old = CharField(required=False)
    new = CharField(required=False)
    confirm = CharField(required=False)

    def clean_confirm(self):
        new = self.cleaned_data.get('new')
        confirm = self.cleaned_data.get('confirm')
        if new != confirm:
            raise ValidationError("The new password does not match the old one.")

    def clean_new(self):
        return make_password(self.cleaned_data.get('new'))

    def update(self , user):
        password = self.cleaned_data.get('new')
        User.objects.filter(pk=user.id).update(password=password)

class OrderForm(Form):
    last_name = CharField(max_length=255)
    phone_number = CharField(max_length=20)
    product_id = IntegerField()
    owner_id = IntegerField(required=False)
    thread_id = IntegerField(required=False)


    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number")
        return "+" + re.sub('\D', "", phone_number)

    def save(self , deliver_price):
        order = Order.objects.create(**self.cleaned_data)
        order.amount = deliver_price + order.product.price*order.quantity
        order.save()
        return order

class ThreadForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].required = False

    class Meta:
        model = Thread
        fields = 'name', 'discount_sum', 'product', 'user'

    def clean_discount_sum(self):

        discount_sum = self.cleaned_data.get('discount_sum')
        product_id = self.data.get('product')
        product = Product.objects.filter(pk=product_id).first()
        if product.sell_price < discount_sum:
            raise ValidationError("Chegirma miqdori berilgandan ko'p")
        return discount_sum

class OperatorForm(Form):
    category_id = CharField(required=False)
    district_id = CharField(required=False)

class OrderModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['comment_operator'].required = False

    class Meta:
        model = Order
        fields = 'quantity', 'send_date', 'district', 'status', 'comment_operator'


class PaymentModelForm(ModelForm):
    def init(self, *args, **kwargs):
        super().init(*args, **kwargs)
        self.fields['user'].required = False

    class Meta:
        model = Payment
        fields = ('amount', 'card_number', 'user')

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')

        if amount< 100000:
            raise ValidationError("Minimal summa 100 ming so'm")
        return amount

    def clean_card_number(self):
        card_number = self.cleaned_data.get('card_number')
        if not card_number.isdigit() or len(card_number) != 16:
            raise ValidationError("Karta nomerda muomo bor")
        return card_number