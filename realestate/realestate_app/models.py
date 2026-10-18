from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.


class RealEstateUser(AbstractUser):
    name = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=20, choices=[('Admin', 'Admin'), ('Agent', 'Agent'), ('Block', 'Block')])
    previous_role = models.CharField(max_length=50, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    department = models.CharField(max_length=100, null=True, blank=True)
    profile_photo = models.ImageField(upload_to='profile_photos/',blank=True,null=True)
    designation = models.CharField(max_length=100,blank=True,null=True)
    bio = models.TextField(blank=True,null=True)
    facebook_link = models.URLField(blank=True,null=True)
    linkedin_link = models.URLField(blank=True,null=True)
    instagram_link = models.URLField(blank=True,null=True)
    twitter_link = models.URLField(blank=True,null=True)
    

    def __str__(self):
        return self.username


class PropertyCategory(models.Model):
    category_name = models.CharField(max_length=100)

    def __str__(self):
        return self.category_name



class Property(models.Model):

    PROPERTY_TYPE = (
        ('Sale', 'Sale'),
        ('Rent', 'Rent'),
    )

    PROPERTY_STATUS = (
        ('Available', 'Available'),
        ('Sold', 'Sold'),
        ('Rented', 'Rented'),
    )

    property_code = models.CharField(
        max_length=50,
        unique=True
    )

    title = models.CharField(max_length=200)

    category = models.ForeignKey(
        PropertyCategory,
        on_delete=models.CASCADE
    )

    agent = models.ForeignKey(
        RealEstateUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'Agent'}
    )

    property_type = models.CharField(
        max_length=20,
        choices=PROPERTY_TYPE
    )

    description = models.TextField(blank=True, null=True)

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )

    location = models.CharField(max_length=255)

    bedrooms = models.IntegerField(
        blank=True,
        null=True
    )


    bathrooms = models.IntegerField(
        blank=True,
        null=True
    )

    area_sqft = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=PROPERTY_STATUS,
        default='Available'
    )

    video_tour = models.FileField(
        upload_to='property_videos/',
        blank=True,
        null=True
    )

    featured_property = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.title



class PropertyImage(models.Model):

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='images'
    )

    image = models.ImageField(
        upload_to='property_images/'
    )

    def __str__(self):
        return self.property.title



class CustomerInquiry(models.Model):

    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Assigned', 'Assigned'),
        ('Replied', 'Replied'),
        ('Under Review', 'Under Review'),
    )

    inquiry_code = models.CharField(max_length=20, unique=True)

    full_name = models.CharField(max_length=100)

    email = models.EmailField()

    subject = models.CharField(max_length=200)

    message = models.TextField()

    assigned_to = models.ForeignKey(
        RealEstateUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={
            'role__in': ['Admin', 'Agent']
        }
    )

    reply = models.TextField(
        blank=True,
        null=True
    )

    replied_by = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    replied_at = models.DateTimeField(
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.inquiry_code} - {self.full_name}"