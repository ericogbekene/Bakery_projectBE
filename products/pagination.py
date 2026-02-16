from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination for product lists.
    - Page size: 20 items per page
    - Client can override page size with `page_size` parameter
    - Max page size: 100
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        """
        Return paginated response with additional metadata.
        """
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('page_size', self.page.paginator.per_page),
            ('results', data),
        ]))


class SmallResultsSetPagination(PageNumberPagination):
    """
    Smaller pagination for compact lists.
    - Page size: 10 items per page
    - No client override
    """
    page_size = 10


class LargeResultsSetPagination(PageNumberPagination):
    """
    Larger pagination for admin views.
    - Page size: 50 items per page
    - Client can override up to 200
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200