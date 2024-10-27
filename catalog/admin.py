from django.contrib import admin

from .models import Author, Genre, Book, BookInstance, Language

# admin.site.register(Author)


class BooksInLine(admin.TabularInline):
    model = Book.author.through
    extra = 0


class AuthorAdmin(admin.ModelAdmin):
    list_display = ["last_name", "first_name",
                    "date_of_birth", "date_of_death"]
    fields = ["first_name", "last_name", ("date_of_birth", "date_of_death")]
    inlines = [BooksInLine]


class BooksInstanceInLine(admin.TabularInline):
    model = BookInstance
    extra = 0
    fields = ["book", "id", "status", "due_back"]


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ["title", "display_author", "display_genre"]
    inlines = [BooksInstanceInLine]


@admin.register(BookInstance)
class BookInstanceAdmin(admin.ModelAdmin):
    list_display = ["book", "status", "borrower", "due_back", "id"]
    list_filter = ["status", "due_back"]
    fieldsets = [
        (None,
         {"fields": ["book", "id"]},
         ),
        ("Availability",
         {"fields": ["status", "due_back", "borrower"]}
         )
    ]


admin.site.register(Author, AuthorAdmin)
admin.site.register(Genre)
# admin.site.register(Book)
# admin.site.register(BookInstance)
admin.site.register(Language)
