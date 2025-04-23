from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from datetime import datetime

from .models import User, Category, Listing, Comment, Bid

def listing(request, id):
    listingdb = Listing.objects.get(pk=id)
    iswatched = request.user in listingdb.watchlist.all()
    comments = Comment.objects.filter(listing = listingdb)
    owned = request.user.username == listingdb.owner.username
    return render(request, "auctions/listing.html",{
        "listing": listingdb,
        "iswatched": iswatched,
        "comments": comments,
        "owned":owned
    })

def removelisting(request, id):
    in_user = request.user
    listingdb = Listing.objects.get(pk=id)
    listingdb.status = False
    listingdb.save()
    owned = request.user.username == listingdb.owner.username
    iswatched = request.user in listingdb.watchlist.all()
    comments = Comment.objects.filter(listing = listingdb)
    return render(request, "auctions/listing.html",{
        "listing": listingdb,
        "comments": comments,
        "owned":owned,
        "message": "Auction is closed! Item sold",
        "iswatched": iswatched,
        "update":True
    })
    

def comment(request, id):
    listing = Listing.objects.get(pk=id)
    writer = request.user
    message = request.POST['message']

    now = datetime.now()
    Newcomment = Comment(writer=writer, listing=listing, message=message, data=now)
    Newcomment.save() 

    comments = Comment.objects.filter(listing=listing)
    return HttpResponseRedirect(reverse("listing", args=(id, )), {
        "comments":comments
    })

def watchlist(request):
    in_user = request.user
    watched = Listing.objects.filter(watchlist=in_user)
    return render(request, "auctions/watchlist.html", {
        "listings":watched
    })


def remove(request, id):
    listingdb = Listing.objects.get(pk=id)
    in_user = request.user
    listingdb.watchlist.remove(in_user)
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def add(request, id):
    listingdb = Listing.objects.get(pk=id)
    in_user = request.user
    listingdb.watchlist.add(in_user)
    return HttpResponseRedirect(reverse("listing", args=(id, )))
        

def addbid(request, id):
    newbid = float(request.POST['newbid'])     
    listingdb = Listing.objects.get(pk=id)
    iswatched = request.user in listingdb.watchlist.all()
    comments = Comment.objects.filter(listing = listingdb)
    owned = request.user.username == listingdb.owner.username
    #check if the new bid is bigger than update
    if newbid > listingdb.price.bid:
        updatebid = Bid(user=request.user, bid=newbid)
        updatebid.save()
        listingdb.price = updatebid
        listingdb.save()
        return render(request, "auctions/listing.html", {
            "listing": listingdb,
            "message":"Bid placed successfully",
            "iswatched": iswatched,
            "comments": comments,
            "owned":owned
        })
    else:
        return render(request, "auctions/listing.html", {
            "listing": listingdb,
            "message":"Failed, try to bid higher",
            "iswatched": iswatched,
            "comments": comments,
            "owned":owned
        })
        
def index(request):
    active = Listing.objects.filter(status=True)
    categoriesdb = Category.objects.all()
    return render(request, "auctions/index.html", {
        "listings":active,
        "categories":categoriesdb
    })

def chosen(request):
        if request.method == "POST":
            catchosen = request.POST.get('category', None)
            categoriesdb = Category.objects.all()
            if catchosen is None:
                active = Listing.objects.filter(status=True)
            else:
                category = Category.objects.get(categoryname=catchosen)
                active = Listing.objects.filter(status=True, category=category)  

            return render(request, "auctions/index.html", {
                "listings":active,
                "categories":categoriesdb
            })       
         
 
def createlisting(request):
    if request.method == "GET":
        categoriesdb = Category.objects.all()
        return render(request, "auctions/create.html", {
            "categories":categoriesdb
        })
    
    else:
        #get data from db
        title = request.POST["title"]
        description = request.POST["description"]
        category = request.POST["category"]
        price = request.POST["startbid"]
        image = request.POST["image"]

        #get the user
        in_user = request.user

        #get the category-from CS50.ai - if the category does not exist, crate it
        categorydb, created = Category.objects.get_or_create(categoryname=category)

        #save new Bid in database
        bid = Bid(bid=float(price), user=in_user)
        bid.save()

        #save new listing in database
        newlisting = Listing(title=title, description=description, image=image, category=categorydb, price=bid, owner=in_user)
        newlisting.save()
        
        return HttpResponseRedirect(reverse(index))
    

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
