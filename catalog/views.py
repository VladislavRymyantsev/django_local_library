import datetime
from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.contrib.auth.decorators import permission_required
from .forms import RenewBookForm
from .models import Author, Genre, Book, BookInstance


class BookListView (generic.ListView):
    paginate_by = 10
    model = Book


class AuthorListView (generic.ListView):
    paginate_by = 10
    model = Author


def index(request):
    """
    Display function for the site's home page.
    """
    number_of_books = Book.objects.all().count()
    book_count = Book.objects.filter(title__icontains="Робинзон").count()
    number_of_book_instances = BookInstance.objects.all().count()
    number_of_available_book_instances = BookInstance.objects.filter(
        status__exact="a").count()
    number_of_authors = Author.objects.all().count()
    number_of_visits = request.session.get("number_of_visits", 0)
    request.session["number_of_visits"] = number_of_visits+1
    return render(request, "index.html", context={"number_of_books": number_of_books,
                                                  "number_of_books_with_word": book_count,
                                                  "number_of_book_instances": number_of_book_instances,
                                                  "number_of_available_book_instances": number_of_available_book_instances,
                                                  "number_of_authors": number_of_authors,
                                                  "number_of_visits": number_of_visits,
                                                  })


class BookDetailView (generic.DetailView):
    model = Book


class AuthorDetailView (generic.DetailView):
    model = Author


class LoanedBooksByUserListView (LoginRequiredMixin, generic.ListView):
    """
    Класс представление выданных книг по пользователю в виде списка
    """
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10
    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact="o").order_by("due_back")


class LoanedBooksByAllUsersListView (PermissionRequiredMixin, generic.ListView):
    """
    Класс представление выданных книг по всем пользователям в виде списка
    """
    model = BookInstance
    template_name = 'catalog/bookinstance_list_borrowed_all_users.html'
    paginate_by = 10
    permission_required = ('catalog.can_mark_returned')
    def get_queryset(self):
        return BookInstance.objects.filter(status__exact="o").order_by("due_back")


@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    book_inst = get_object_or_404(BookInstance, pk=pk)
    if request.method == 'POST':
        form = RenewBookForm(request.POST)
        if form.is_valid():
            book_inst.due_back = form.cleaned_data['renewal_date']
            book_inst.save()
            return HttpResponseRedirect(reverse('all-borrowed'))
    else:
        proposed_renewal_date = datetime.date.today()+datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})
    return render(request, 'catalog/book_renew_librarian.html', {"form": form, "bookinst": book_inst})


class AuthorCreate(PermissionRequiredMixin, CreateView):

    model = Author
    fields = "__all__"
    initial = {"date_of_death": '12/10/2016'}
    permission_required = 'catalog.can_mark_returned'


class AuthorUpdate(UpdateView):

    model = Author
    fields = ["first_name", "last_name", "date_of_birth", "date_of_death"]
    

class AuthorDelete(DeleteView):

    model = Author
    success_url = reverse_lazy("authors")


class BookCreate(CreateView):

    model = Book
    fields = "__all__"


class BookUpdate(UpdateView):

    model = Book
    fields = "__all__"
    

class BookDelete(DeleteView):

    model = Book
    success_url = reverse_lazy("books")