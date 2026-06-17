from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Постраничная разбивка по умолчанию: 20 элементов на страницу, максимум 100."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
