from collections import OrderedDict

from rest_framework.pagination import PageNumberPagination


class ProductListPaginator(PageNumberPagination):
    page_query_param = 'p'
    page_size = 20
    max_page_size = 30

    def get_paginated_response(self, data):
        try:
            next_page = self.page.next_page_number()
        except:
            next_page = None
        return OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('next_page', next_page),
        ])

class ProductSearchPaginator(ProductListPaginator):
    pass
