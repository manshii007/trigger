from rest_framework import pagination
from rest_framework.response import Response


class CustomPagination(pagination.PageNumberPagination):
    def paginate_queryset(self, queryset, request, view=None):
        self.queryset = queryset
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        approval_count = self.queryset.filter(is_approved="yes").count()
        disapproval_count = self.queryset.filter(is_approved="no").count()
        new_count = self.queryset.filter(is_approved="false").count()

        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'results': data,
            'approved': approval_count,
            'disapproved': disapproval_count,
            'new': new_count
        })


class ShortResultsSetPagination(pagination.PageNumberPagination):
    page_size = 24
    page_size_query_param = 'page_size'
    max_page_size = 100
