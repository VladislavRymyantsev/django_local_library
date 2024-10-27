from django.db import models
from django.urls import reverse
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower
from django.contrib.auth.models import User
import uuid
from datetime import date


class Genre(models.Model):
    """
    Genre of book model.
    """
    name = models.CharField(
        max_length=50, help_text="Enter genre of book", unique=True)

    def __str__(self):
        """
        Предоставление строки обекту модели.
        """
        return self.name

    def get_absolute_url(self):
        """
        Returns the url to access a particular genre instance.
        """
        return reverse('genre-detail', args=[str(self.id)])

    class Meta:

        constraints = [
            UniqueConstraint(Lower('name'),
                             name='genre_name_case_insensitive_unique',
                             violation_error_message="Genre already exists"
                             )]


class Author(models.Model):
    first_name = models.CharField(
        max_length=100, help_text="Enter first name of author of book")
    last_name = models.CharField(
        max_length=100, help_text="Enter last name of author of book")
    date_of_birth = models.DateField(null=True, blank=True)
    date_of_death = models.DateField("Died", null=True, blank=True)

    def get_absolute_url(self):
        """
        Returns the url to access a particular author instance.
        """
        return reverse('author-detail', args=[str(self.id)])

    def __str__(self):
        """
        Предоставление строки обекту модели.
        """
        return f"{self.last_name}, {self.first_name}"

    class Meta:

        ordering = ['last_name', 'first_name']


class Language(models.Model):

    name = models.CharField(
        max_length=100, help_text="Enter the language of the book", unique=True)

    def __str__(self):
        """
        Предоставление строки обекту модели.
        """
        return self.name

    def get_absolute_url(self):
        """
        Returns the url to access a particular language instance.
        """
        return reverse('language-detail', args=[str(self.id)])

    class Meta:

        constraints = [
            UniqueConstraint(Lower('name'),
                             name='language_name_case_insensitive_unique',
                             violation_error_message="Language already exists"
                             )]


class Book(models.Model):

    title = models.CharField(max_length=120, help_text="Title of the book")
    summary = models.TextField(
        max_length=1000, help_text="Type the descripion of the book")
    isbn = models.CharField('ISBN', max_length=13,
                            unique=True, help_text="Enter the isbn of the book")
    author = models.ManyToManyField(
        Author, help_text="Enter the autor(-s) of the book")
    genre = models.ManyToManyField(
        Genre, help_text="Enter the genre of the book")
    language = models.ForeignKey(
        Language, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        """
        Предоставление строки обекту модели.
        """
        return self.title

    def get_absolute_url(self):
        """
        Returns the url to access a particular book instance.
        """
        return reverse('book-detail', args=[str(self.id)])

    def display_genre(self):
        """
        Creates a string for the Genre.
        """
        return ", ".join([genre.name for genre in self.genre.all()])
    display_genre.short_description = "Genre"

    def display_author(self):
        """
        Creates a string for the Author.
        """
        return ", ".join([f"{author.last_name}, {author.first_name}" for author in self.author.all()])
    display_author.short_description = "Author"

    class Meta:
        ordering = ["title"]


class BookInstance(models.Model):
    """
    Model representing a specific copy of a book
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        help_text="Unique ID for this particular book across whole library"
    )

    book = models.ForeignKey(Book, on_delete=models.RESTRICT)
    due_back = models.DateField(null=True, blank=True)
    LOAN_STATUS = [
        ('m', 'Maintenance'),
        ('o', 'On loan'),
        ('a', 'Available'),
        ('r', 'Reserved')
    ]
    status = models.CharField(
        max_length=1,
        choices=LOAN_STATUS,
        blank=True,
        default="m",
        help_text="Book Availability"
    )
    borrower = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        """
        String representing the book instance
        """
        return f"{self.id} ({self.book.title})"

    def get_absolute_url(self):
        """
        Returns the url to access a particular book instance.
        """
        return reverse('bookinstance-detail', args=[str(self.id)])

    @property
    def is_overdue(self):
        if self.due_back and date.today()>self.due_back:
            return True
        return False

    class Meta:

        ordering = ["due_back"]
        permissions = [("can_mark_returned", "Set book as returned")]
