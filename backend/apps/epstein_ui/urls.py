from django.urls import path
from django.urls import re_path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("random-pdf/", views.random_pdf, name="random_pdf"),
    path("search-pdf/", views.search_pdf, name="search_pdf"),
    path("search-suggestions/", views.search_suggestions, name="search_suggestions"),
    path("browse/", views.browse, name="browse"),
    path("browse-list/", views.browse_list, name="browse_list"),
    path("register/", views.register, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("username-check/", views.username_check, name="username_check"),
    path("annotations/", views.annotations_api, name="annotations_api"),
    path("annotation-votes/", views.annotation_votes, name="annotation_votes"),
    path("annotation-comments/", views.annotation_comments, name="annotation_comments"),
    path("comment-votes/", views.comment_votes, name="comment_votes"),
    path("comment-delete/", views.delete_comment, name="comment_delete"),
    path("pdf-comments/", views.pdf_comments, name="pdf_comments"),
    path("pdf-comment-votes/", views.pdf_comment_votes, name="pdf_comment_votes"),
    path("pdf-comment-replies/", views.pdf_comment_replies, name="pdf_comment_replies"),
    path("pdf-reply-votes/", views.pdf_reply_votes, name="pdf_reply_votes"),
    path("pdf-reply-delete/", views.pdf_reply_delete, name="pdf_reply_delete"),
    path("pdf-votes/", views.pdf_votes, name="pdf_votes"),
    re_path(r"^(?P<pdf_slug>[A-Za-z0-9_-]+)$", views.index, name="index_pdf"),
]
