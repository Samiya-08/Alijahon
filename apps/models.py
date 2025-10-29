# from ckeditor_uploader.fields import RichTextUploadingField
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractUser, UserManager
from django.db.models import Model, CharField, ForeignKey, DecimalField, ImageField, DateTimeField, CASCADE, TextField, \
    IntegerField, SET_NULL, BigIntegerField, TextChoices, SlugField, SmallIntegerField, DateField
from django.utils.text import slugify


class CustomUserManager(UserManager):
    def _create_user(self,phone_number, password, **extra_fields):
        if not phone_number:
            raise ValueError("The given phone number must be set")

        user = self.model(phone_number=phone_number, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self,phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(phone_number, password, **extra_fields)

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(phone_number, password, **extra_fields)

class BaseSlugModel(Model):
    name = CharField(max_length=255)
    slug = SlugField(max_length=255, unique=True , blank=True , null=True)
    class Meta:
        abstract = True
    def save(self, **kwargs):
        slug = slugify(self.name)
        i = 1
        while Category.objects.filter(slug=slug).exists():
            slug += f"-{i}"
            i+=1
        self.slug = slug
        super().save()

class User(AbstractUser):
    class RoleType(TextChoices):
        ADMIN = 'admin', 'Admin'
        USER = 'user', 'User'
        OPERATOR = 'operator', 'Operator'
    objects = CustomUserManager()
    USERNAME_FIELD = 'phone_number'
    username = None
    phone_number = CharField(max_length=20, unique=True)
    district = ForeignKey('apps.District', on_delete=SET_NULL, null=True, blank=True)
    address = TextField()
    telegram_id = BigIntegerField(unique=True , blank=True , null=True)
    about = TextField(blank=True, null=True)
    role = CharField(max_length=10, choices=RoleType, default=RoleType.USER)
    balance = DecimalField(max_digits=10, decimal_places=0, default=0)



class Region(Model):
    name = CharField(max_length=255)

class District(Model):
    name = CharField(max_length=255)
    region = ForeignKey('apps.Region', on_delete=CASCADE)

class Category(BaseSlugModel):
    icon = CharField(max_length=255)

    def __str__(self):
        return self.name

class Product(BaseSlugModel):
    description = TextField()
    price = DecimalField(max_digits=10, decimal_places=2)
    image = ImageField(upload_to='products/')
    category = ForeignKey('apps.Category', on_delete=CASCADE)
    sell_price = DecimalField(max_digits=10 , decimal_places=0 , default=0)
    quantity = SmallIntegerField(default=1)
    sale = CharField(max_length=50 , default=None , null=True , blank=True)
    telegram_url = CharField(max_length=50 , null=True , blank=True)
    discount = SmallIntegerField(default=0)


class Wishlist(Model):
    user = ForeignKey(User, on_delete=CASCADE)
    product = ForeignKey('apps.Product', on_delete=CASCADE)

class Thread(Model):
    user = ForeignKey(User, on_delete=CASCADE)
    product = ForeignKey('apps.Product', on_delete=CASCADE)
    discount_sum = DecimalField(max_digits=10, decimal_places=2)
    name = CharField(max_length=255)
    created_at = DateTimeField(auto_now_add=True)
    visit_count = IntegerField(default=0)

    @property
    def product_price(self):
        return self.product.price - self.discount_sum


class Order(Model):
    class StatusType(TextChoices):
        NEW = 'new', 'New'
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        CANCELED = 'canceled', 'Canceled'
        READY_TO_ORDER = 'ready_to_order', 'Ready To Order'
        DELIVERING = 'delivering', 'Delivering'
        DELIVERED = 'delivered', 'Delivered'
        ARCHIVED = 'archived', 'Archived'
        NOT_PICK_UP = 'not_pick_up', 'Not Pick Up'

    last_name = CharField(max_length=255)
    owner = ForeignKey('apps.User', on_delete=SET_NULL, null=True, blank=True , related_name='orders')
    phone_number = CharField(max_length=20)
    ordered_at = DateTimeField(auto_now_add=True)
    thread = ForeignKey('apps.Thread', on_delete=SET_NULL, null=True, blank=True , related_name='orders')
    product = ForeignKey('apps.Product', on_delete=CASCADE , related_name='orders')
    quantity = IntegerField(default=1)
    status = CharField(max_length=20, choices=StatusType , default=StatusType.NEW)
    amount = DecimalField(max_digits=10 , decimal_places=0 , default=0 , null=True , blank=True)
    updated_at = DateTimeField(auto_now=True)
    district = ForeignKey('apps.District', SET_NULL, related_name='orders', null=True, blank=True)
    comment_operator = TextField(default = '')
    send_date = DateField(null=True, blank=True)
    operator = ForeignKey('apps.User', SET_NULL, null=True, blank=True, related_name = 'operator_orders')
    delivery_date =ForeignKey('apps.User', SET_NULL, null=True, blank=True, related_name = 'deliver_orders')




    @property
    def amount_summa(self):
        return self.quantity * self.product.price

    @property
    def discount_sum(self):
        summa = self.product.price * self.product.discount / 100
        if self.thread:
            summa+=self.thread.discount_sum
        return summa

class Payment(Model):
    class StatusType(TextChoices):
        REVIEW = 'review', 'Review'
        COMPLETED = 'completed', 'Completed'
        CANCEL = 'cancel', 'Cancel'

    user = ForeignKey('apps.User', on_delete=CASCADE, related_name='payments')
    amount = DecimalField(max_digits=10, decimal_places=2)
    check_payment = ImageField(upload_to='payment/', null=True, blank=True)
    card_number = CharField(max_length=16)
    payment_at = DateTimeField(auto_now_add=True)
    status = CharField(max_length=10, choices=StatusType , default=StatusType.REVIEW)
    description = TextField(blank=True, null=True)

class AdminSetting(Model):
    deliver_price = DecimalField(max_digits=5 ,decimal_places=0)
    competition_photo = ImageField(upload_to='admin/')
    start = DateField()
    finish = DateField()
    description = TextField()