from django.db import models
from django.contrib.auth.models import User
import random
import string

# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    barcode = models.CharField(max_length=20, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.barcode:
            # Generate a unique 8-digit numeric barcode for the user
            while True:
                new_barcode = ''.join(random.choices(string.digits, k=8))
                if not Profile.objects.filter(barcode=new_barcode).exists():
                    self.barcode = new_barcode
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.username} Profile'

class Item(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    quantity = models.PositiveIntegerField(default=0)
    barcode = models.CharField(max_length=20, unique=True, blank=True)
    image = models.ImageField(upload_to='item_images/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.barcode:
            # Generate a unique 12-digit numeric barcode
            while True:
                new_barcode = ''.join(random.choices(string.digits, k=12))
                if not Item.objects.filter(barcode=new_barcode).exists():
                    self.barcode = new_barcode
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Borrowing(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    initial_quantity = models.PositiveIntegerField(default=0) # New field to store original quantity
    quantity = models.PositiveIntegerField()
    borrow_date = models.DateTimeField(auto_now_add=True)
    return_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} borrowed {self.quantity} of {self.item.name}"
