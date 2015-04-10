from django.shortcuts import redirect, render
from subsystems.db.models import User
from .utils import ContextTest


def test_signup(request):
    name = request.GET["n"]
    email = request.GET["e"]
    password = request.GET["p"]

    ctx = ContextTest()

    try:
        u = User.objects.create_user(email=email, password=password, name=name)
        ctx.out("id", u.id).out("email", u.email).out("name", u.name)
    except Exception as e:
        ctx.out("error", e)
    return render(request, "test.html", ctx.dict())


def test_signin(request):
    email = request.GET["e"]
    password = request.GET["p"]

    u = User.objects.login(request, email, password)

    ctx = ContextTest()

    if u is None:
        ctx.out("error", "access denied")
    else:
        ctx.out("id", u.id).out("email", u.email).out("name", u.name)

    return render(request, "test.html", ctx.dict())


def test_is_auth(request):
    a = request.user.is_authenticated()
    ctx = ContextTest()
    ctx.out("is_auth", a)
    return render(request, "test.html", ctx.dict())