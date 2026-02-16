from django.contrib import admin
from .models import BannedUser, PdfDocument, Annotation, PdfComment, SolanaWallet


@admin.register(BannedUser)
class BannedUserAdmin(admin.ModelAdmin):
    list_display = ("username", "reason", "created_at")
    search_fields = ("username", "reason")
    ordering = ("-created_at",)


@admin.register(SolanaWallet)
class SolanaWalletAdmin(admin.ModelAdmin):
    list_display = ("wallet_address", "user", "is_primary", "created_at")
    search_fields = ("wallet_address", "user__username")
    list_filter = ("is_primary",)
    ordering = ("-created_at",)


@admin.register(PdfDocument)
class PdfDocumentAdmin(admin.ModelAdmin):
    list_display = ("filename", "annotation_count", "comment_count", "vote_score")
    search_fields = ("filename",)


@admin.register(Annotation)
class AnnotationAdmin(admin.ModelAdmin):
    list_display = ("pdf_key", "user", "created_at")
    list_filter = ("user",)
    search_fields = ("pdf_key", "user__username", "note")


@admin.register(PdfComment)
class PdfCommentAdmin(admin.ModelAdmin):
    list_display = ("pdf", "user", "body", "created_at")
    list_filter = ("user",)
    search_fields = ("pdf__filename", "user__username", "body")