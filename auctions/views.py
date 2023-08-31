from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django import forms
from django.db.models import Max
from django.contrib import messages

from .models import User, Listing, Bid, Watchlist

## form class for login of users
class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': "form-control",
                                                             "placeholder":"username",
                                                             'autofocus': True}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': "form-control",
                                                                 "placeholder":"password"}))


## form class for register of users
class RegisterForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': "form-control",
                                                             "placeholder":"username",
                                                             'autofocus': True}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': "form-control",
                                                            "placeholder":"email"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': "form-control",
                                                                 "placeholder":"password"}))
    confirmation = forms.CharField(widget=forms.PasswordInput(attrs={'class': "form-control",
                                                                     "placeholder":"confirmation"}))
    
class ListingForm(forms.ModelForm):

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = "form-control"
            visible.field.widget.attrs['placeholder'] = visible.field.label

    class Meta:
        model = Listing
        fields = ["title","description","price","photo","category"]

class BidForm(forms.Form):
    bid_amount = forms.FloatField(widget=forms.NumberInput(attrs={'class': "form-control", 
                                                        "placeholder":"Bid amount"}))


def index(request):
    listings = Listing.objects.annotate(max_price = Max("bids__bid_amount"))
    return render(request, "auctions/index.html",context={"listings":listings})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            # username = request.POST['username']
            # password = request.POST['password']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username = username, password = password)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect(reverse('index'))
            else:
                form = LoginForm()
                return render(request, "auctions/login.html",context={'form':form, "message":"Invalid username and/or password."})
        else:
            return render(request, "auctions/login.html",context={'form':form,"message":"invalid form"})
    
    else:
        form = LoginForm()
        return render(request, "auctions/login.html",context={'form':form})


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            email = form.cleaned_data['email']
            if form.cleaned_data['password'] != form.cleaned_data['confirmation']:
                form = RegisterForm()
                return render(request, 'auctions/register.html',context={"form":form,"message":"Passwords must match."})
            
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
            except IntegrityError:
                form = RegisterForm()
                return render(request, "auctions/register.html", context = {"form":form,"message": "Username already taken"})
            
            login(request, user)
            return HttpResponseRedirect(reverse("index"))

        else:
            form = RegisterForm()
            return render(request, 'auctions/register.html',context={"form":form})
        
    else:
        form = RegisterForm()
        return render(request, 'auctions/register.html',context={"form":form})
    

def create_listing(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    else:
        if request.method == "POST":
            form = ListingForm(request.POST)
            new_listing = form.save(commit = False)
            new_listing.user = User.objects.get(pk = request.user.pk)
            new_listing.save()
            Bid.objects.create(bidder = User.objects.get(pk = request.user.pk),
                                           listing = new_listing,
                                           active =True,
                                           bid_amount = new_listing.price)
            return HttpResponseRedirect(reverse("index"))

        else:
            form = ListingForm()
            return render(request,'auctions/create_listing.html',context={"form":form})
        
def listing_view(request,item):
    if  not Listing.objects.filter(pk=item).exists():
        return render(request, "auctions/item_not_found.html", context = {"item":item})
    
    # Retreave listing from db table
    lis = Listing.objects.get(pk = item)
    # Retreave the current highest bid for the current listing
    curr_bid = Bid.objects.filter(listing = lis, active = True).order_by('-bid_amount').first()
    if request.user.is_authenticated:
        usr = User.objects.get(pk = request.user.pk)
        is_owner = usr.pk == lis.user.pk
        # item is in the watchlist?
        in_watchlist = Watchlist.objects.filter(user =usr,listing = lis)
        if request.method == "POST" and "place-bid-btn" in request.POST:
            # check if the form is valid
            bid_form = BidForm(request.POST)    
            if bid_form.is_valid():
                bid_amount = bid_form.cleaned_data["bid_amount"]
                if bid_amount > curr_bid.bid_amount:
                    # set the active field to false for previous bids.
                    Bid.objects.filter(listing = lis, active = True).update(active = False)
                    # create a new bid instance.
                    Bid.objects.create(bidder = usr,
                                                 listing = lis,
                                                 bid_amount = bid_amount,
                                                 active = True)
                    bid_form = BidForm()
                    messages.success(request,"Bid Placed!")
                    return HttpResponseRedirect(reverse("item",kwargs={"item":item}))

                else:
                    messages.warning(request, "Enter a larger price!")
                    return HttpResponseRedirect(reverse("item",kwargs={"item":item}))

            # if the form is not valid then render the page with the error of the form.
            return render(request,"auctions/item.html",context = {"bid":curr_bid,
                                                                  "bid_form":bid_form,
                                                                  "in_watchlist": in_watchlist})
    
        elif request.method == "POST" and "watchlist-add-btn" in request.POST:
            if not in_watchlist:
                Watchlist.objects.create(user = usr,listing = lis)
                return HttpResponseRedirect(reverse("item",kwargs={"item":item}))
            # return info that the item is already on the watchlist.
            else:
                return HttpResponseRedirect(reverse("item",kwargs={"item":item}))
        
        # todo: verify that the item is in the watchlist of the user
        elif request.method == "POST" and "watchlist-del-btn" in request.POST:
            if in_watchlist:
                Watchlist.objects.filter(user = usr,listing = lis).delete()
                return HttpResponseRedirect(reverse("item",kwargs={"item":item}))
            # return info that the item is not on the watchlist.
            else:
                return HttpResponseRedirect(reverse("item",kwargs={"item":item}))
        # if the user is authenticated but no post request

        elif request.method == "POST" and "close-bid-btn" in request.POST and is_owner:
            lis.active = False
            lis.winner = curr_bid.bidder
        else:
            bid_form = BidForm()
            if is_owner:
                return render(request,"auctions/item.html",context = {"bid_form":bid_form,
                                                                    "bid":curr_bid,
                                                                    "in_watchlist": in_watchlist,
                                                                    "owner":is_owner})
            return render(request,"auctions/item.html",context = {"bid_form":bid_form,
                                                                    "bid":curr_bid,
                                                                    "in_watchlist": in_watchlist,
                                                                    "owner":is_owner})
    # if the user is not authenticated
    else:
        bid_form = BidForm()
        return render(request,"auctions/item.html",context = {"bid_form":bid_form,"bid":curr_bid})
    
