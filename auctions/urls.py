from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("listing",views.create_listing, name = "listing"),
    path("listing/<int:item>",views.listing_view, name = "item"),
    path("watchlist/<int:user>",views.watchlist_view, name = "watchlist")
]
