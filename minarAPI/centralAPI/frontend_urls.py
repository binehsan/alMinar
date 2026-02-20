from django.urls import path
from . import frontend_views

urlpatterns = [
    path("", frontend_views.home, name="home"),
    path("explore/", frontend_views.explore, name="explore"),
    path("masjid/<uuid:masjid_id>/", frontend_views.masjid_detail, name="masjid-detail"),
    path("verify/<uuid:token>/page/", frontend_views.verify_page, name="verify-page"),
    path("about/", frontend_views.about, name="about"),
    path("report/", frontend_views.report_page, name="report"),

    # Auth
    path("login/", frontend_views.login_page, name="login"),
    path("register/", frontend_views.register_page, name="register"),
    path("logout/", frontend_views.logout_view, name="logout"),

    # Dashboard
    path("dashboard/", frontend_views.dashboard, name="dashboard"),

    # Dashboard actions
    path("dashboard/add-favourite/", frontend_views.add_favourite, name="add-favourite"),
    path("dashboard/remove-favourite/<uuid:fav_id>/", frontend_views.remove_favourite, name="remove-favourite"),
    path("dashboard/send-signal/", frontend_views.send_signal, name="send-signal"),
    path("dashboard/upload-document/", frontend_views.upload_document, name="upload-document"),
    path("dashboard/upload-prayer-times/", frontend_views.upload_prayer_times, name="upload-prayer-times"),
    path("dashboard/add-masjid/", frontend_views.add_masjid, name="add-masjid"),
]
