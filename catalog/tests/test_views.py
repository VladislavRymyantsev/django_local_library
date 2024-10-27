from django.test import TestCase
from catalog.models import Author, BookInstance, Book, Genre, Language
from django.urls import reverse
import datetime
from django.utils import timezone
from django.contrib.auth.models import User, Permission

class LoanedBooksByUserListViewTest(TestCase):

    def setUp(self):
        test_user1 = User.objects.create_user(username="testuser1", password="12345")
        test_user1.save()
        test_user2 = User.objects.create_user(username="testuser2", password="12345")
        test_user2.save()

        test_author = Author.objects.create(first_name="David", last_name="One")
        test_genre = Genre.objects.create(name="Science fiction")
        test_language = Language.objects.create(name="English")
        test_book = Book.objects.create(title="Cyberpunk", summary="2077", isbn="2079", language=test_language)
        test_book.author.set([test_author])
        test_book.genre.set([test_genre])
        test_book.save()

        number_of_book_copies = 30
        for copy in range(number_of_book_copies):
            return_date = timezone.now()+datetime.timedelta(days=copy%5)
            if copy % 2:
                borrower = test_user1
            else:
                borrower = test_user2
            status = "a"
            BookInstance.objects.create(book=test_book, due_back=return_date, borrower=borrower, status=status)
        
    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse("my-borrowed"))
        self.assertRedirects(resp, "/accounts/login/?next=/catalog/mybooks/")
    
    def test_logged_in_uses_correct_template(self):
        login = self.client.login(username="testuser1", password="12345")
        resp = self.client.get(reverse("my-borrowed"))
        self.assertEqual(str(resp.context["user"]), "testuser1")
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "catalog/bookinstance_list_borrowed_user.html")

    def test_only_borrowed_books_in_list(self):
        login = self.client.login(username="testuser1", password="12345")
        resp = self.client.get(reverse("my-borrowed"))
        self.assertEqual(str(resp.context["user"]), "testuser1")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("bookinstance_list" in resp.context)
        self.assertEqual(len(resp.context["bookinstance_list"]), 0)
        ten_books = BookInstance.objects.all()[:10]
        for book in ten_books:
            book.status = "o"
            book.save()
        resp = self.client.get(reverse("my-borrowed"))
        self.assertEqual(str(resp.context["user"]), "testuser1")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("bookinstance_list" in resp.context)
        for book in resp.context["bookinstance_list"]:
            self.assertEqual(resp.context["user"], book.borrower)
            self.assertEqual("o", book.status)
    
    def test_pages_ordered_by_due_back(self):
        for book in BookInstance.objects.all():
            book.status = "o"
            book.save()
        login = self.client.login(username="testuser1", password="12345")
        resp = self.client.get(reverse("my-borrowed"))
        self.assertEqual(str(resp.context["user"]), "testuser1")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context["bookinstance_list"]), 10)
        last_date = 0
        for book in BookInstance.objects.all():
            if last_date == 0:
                last_date = book.due_back
            else:
                self.assertTrue(last_date<=book.due_back)


class AuthorListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        number_of_authors = 11
        for i in range(number_of_authors):
            Author.objects.create(first_name=f"Name {i}", last_name=f"Surname {i}")
    
    def test_view_url_exists_at_desired_location(self):
        response = self.client.get("/catalog/authors/")
        self.assertEqual(response.status_code, 200)

    def test_view_url_accesable_by_name(self):
        response = self.client.get(reverse("authors"))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse("authors"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/author_list.html")
    
    def test_pagination_is_10(self):
        response = self.client.get(reverse("authors"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertTrue(response.context["is_paginated"]==True)
        self.assertTrue(len(response.context["author_list"])==10)

    def test_lists_all_author(self):
        response = self.client.get(reverse("authors")+'?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertTrue("is_paginated" in response.context)
        self.assertTrue(response.context["is_paginated"]==True)
        self.assertTrue(len(response.context["author_list"])==1)


class RenewBookInstancesViewTest(TestCase):

    def setUp(self):
        test_user1 = User.objects.create_user(username="testuser1", password="12345")
        test_user1.save()
        test_user2 = User.objects.create_user(username="testuser2", password="12345")
        test_user2.save()
        permission = Permission.objects.get(name="Set book as returned")
        test_user1.user_permissions.add(permission)
        test_user1.save()

        test_author = Author.objects.create(first_name="David", last_name="One")
        test_genre = Genre.objects.create(name="Science fiction")
        test_language = Language.objects.create(name="English")
        test_book = Book.objects.create(title="Cyberpunk", summary="2077", isbn="2079", language=test_language)
        test_book.author.set([test_author])
        test_book.genre.set([test_genre])
        test_book.save()
        return_date = datetime.date.today()+datetime.timedelta(days=5)
        self.test_bookinstance1 = BookInstance.objects.create(book=test_book, due_back=return_date, borrower=test_user1, status="o")
        self.test_bookinstance2 = BookInstance.objects.create(book=test_book, due_back=return_date, borrower=test_user2, status="o")

    def test_redirect_if_not_logged_in(self):
        resp = self.client.get(reverse("renew-book-librarian", kwargs={"pk": self.test_bookinstance1.pk}))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith("/accounts/login/"))
    
    def test_redirect_if_logged_in_but_not_correct_permission(self):
        login = self.client.login(username="testuser2", password="12345")
        resp = self.client.get(reverse("renew-book-librarian", kwargs={"pk": self.test_bookinstance2.pk}))
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith("/accounts/login/"))

    def test_logged_in_with_permission_borrowed_book(self):
        login = self.client.login(username="testuser1", password="12345")
        resp = self.client.get(reverse("renew-book-librarian", kwargs={"pk": self.test_bookinstance1.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_logged_in_with_permission_another_users_borrowed_book(self):
        login = self.client.login(username="testuser1", password="12345")
        resp = self.client.get(reverse("renew-book-librarian", kwargs={"pk": self.test_bookinstance2.pk}))
        self.assertEqual(resp.status_code, 200)

    def test_http_404_for_invalid_book_if_logged_in(self):
        import uuid
        test_uuid = uuid.uuid4()
        login = self.client.login(username="testuser1", password="12345")
        resp = self.client.get(reverse("renew-book-librarian", kwargs={"pk": test_uuid}))
        self.assertEqual(resp.status_code, 404)

    def test_uses_correct_template(self):
        login = self.client.login(username="testuser1", password="12345")
        resp = self.client.get(reverse("renew-book-librarian", kwargs={"pk": self.test_bookinstance1.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "catalog/book_renew_librarian.html")

    def test_form_renewal_date_initially_has_date_three_weeks_in_future(self):
        login = self.client.login(username="testuser1", password="12345")
        resp = self.client.get(reverse("renew-book-librarian", kwargs={"pk": self.test_bookinstance1.pk}))
        self.assertEqual(resp.status_code, 200)
        date3weeks = datetime.date.today()+datetime.timedelta(weeks=3)
        self.assertEqual(resp.context["form"].initial["renewal_date"], date3weeks)
    
    def test_rederects_to_all_borrowed_book_list_on_success(self):
        login = self.client.login(username="testuser1", password="12345")
        date2weeks = datetime.date.today()+datetime.timedelta(weeks=2)
        resp = self.client.post(reverse("renew-book-librarian", kwargs={"pk": self.test_bookinstance1.pk}), {"renewal_date": date2weeks})
        self.assertRedirects(resp, reverse("all-borrowed"))

    # def test_form_invalid_renewal_date_past(self):
    #     login = self.client.login(username="testuser1", password="12345")
    #     date1week_past = datetime.date.today()-datetime.timedelta(weeks=1)
    #     resp = self.client.post(reverse("renew-book-librarian", kwargs={"pk": self.test_bookinstance1.pk}), {"renewal_date": date1week_past})
    #     self.assertEqual(resp.status_code, 200)
    #     self.assertFormError(resp, resp.context['form'], "renewal_date", "Invalid date - renewal in past")

    # def test_form_invalid_renewal_date_future(self):
    #     login = self.client.login(username="testuser1", password="12345")
    #     date5weeks = datetime.date.today()+datetime.timedelta(weeks=5)
    #     resp = self.client.post(reverse("renew-book-librarian", kwargs={"pk": self.test_bookinstance1.pk}), {"renewal_date": date5weeks})
    #     self.assertEqual(resp.status_code, 200)
    #     self.assertFormError(resp, resp.context['form'], "renewal_date", "Invalid date - renewal more than 4 weeks ahead")


class AuthorCreateViewTest(TestCase):

    def setUp(self):
        test_user1 = User.objects.create_user(username="testuser1", password="12345")
        test_user1.save()
        test_user2 = User.objects.create_user(username="testuser2", password="12345")
        test_user2.save()
        permission = Permission.objects.get(name="Set book as returned")
        test_user1.user_permissions.add(permission)
        test_user1.save()

    def test_who_allowed(self):
        login = self.client.login(username="testuser1", password="12345")
        resp = self.client.get(reverse("author-create"))
        self.assertEqual(resp.status_code, 200)

    def test_who_not_allowed(self):
        login = self.client.login(username="testuser2", password="12345")
        resp = self.client.get(reverse("author-create"))
        self.assertEqual(resp.status_code, 403)
