from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    id = models.AutoField(primary_key = True)
    

class Listing(models.Model):
    id = models.AutoField(primary_key = True)
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    title = models.CharField(max_length = 200)
    description = models.TextField()
    price = models.FloatField()
    photo = models.URLField(blank = True)
    category = models.CharField(max_length = 20, blank = True)
    active = models.BooleanField(default = True)

class Bid(models.Model):
    id = models.AutoField(primary_key = True)
    bidder = models.ForeignKey(User,on_delete = models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete = models.CASCADE, related_name= "bids")
    bid_amount = models.FloatField()
    active = models.BooleanField(default = False)

class Watchlist(models.Model):
    id = models.AutoField(primary_key = True)
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    listing = models.ForeignKey(Listing, on_delete = models.CASCADE)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'listing'], name='user-listing')
        ]

class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    text = models.TextField()
    user = models.ForeignKey(User,on_delete=models.CASCADE,default = "")
    listing = models.ForeignKey(Listing,on_delete=models.CASCADE)

class Winner(models.Model):
    id = models.AutoField(primary_key = True)
    listing = models.OneToOneField(Listing, on_delete = models.SET_NULL, null = True)
    user = models.OneToOneField(User, on_delete = models.SET_NULL, null = True)  

