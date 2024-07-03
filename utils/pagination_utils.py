import logging
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework.response import Response
from rest_framework import status
from functools import wraps

# Get the logger for this module
logger = logging.getLogger(__name__)


def log_pagination_info(func):
    """
    Decorator to log pagination information.

    This decorator logs the page number and page size for each pagination operation.
    It also logs any errors that occur during pagination.

    Args:
        func (callable): The function to be decorated.

    Returns:
        callable: The wrapped function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            logger.info(f"Pagination performed: page={kwargs.get('page', 'N/A')}, "
                        f"page_size={kwargs.get('page_size', 'N/A')}")
            return result
        except Exception as e:
            logger.exception(f"Error in pagination: {str(e)}")
            raise

    return wrapper


@log_pagination_info
def paginate_queryset(queryset, page=1, page_size=10):
    """
    Paginate a Django queryset.

    This function takes a queryset and returns a paginated version of it.
    It handles errors such as invalid page numbers or empty pages.

    Args:
        queryset (QuerySet): The Django queryset to paginate.
        page (int): The page number to retrieve (default is 1).
        page_size (int): The number of items per page (default is 10).

    Returns:
        tuple: A tuple containing:
            - list: The list of items for the current page.
            - dict: Pagination metadata including current_page, total_pages,
                    total_items, has_next, and has_previous.

    Raises:
        ValueError: If the page number is less than 1.
    """
    if page < 1:
        logger.warning(f"Invalid page number: {page}. Using page 1.")
        page = 1

    paginator = Paginator(queryset, page_size)

    try:
        paginated_queryset = paginator.page(page)
    except EmptyPage:
        logger.warning(f"Page {page} is out of range. Using last page.")
        paginated_queryset = paginator.page(paginator.num_pages)
    except PageNotAnInteger:
        logger.warning(f"Invalid page number: {page}. Using page 1.")
        paginated_queryset = paginator.page(1)

    return list(paginated_queryset), {
        'current_page': paginated_queryset.number,
        'total_pages': paginator.num_pages,
        'total_items': paginator.count,
        'has_next': paginated_queryset.has_next(),
        'has_previous': paginated_queryset.has_previous(),
    }


def get_paginated_response(data, metadata):
    """
    Create a paginated response for API views.

    This function takes paginated data and metadata and returns a
    formatted Response object suitable for API views.

    Args:
        data (list): The paginated data to be included in the response.
        metadata (dict): Pagination metadata including current_page, total_pages,
                         total_items, has_next, and has_previous.

    Returns:
        Response: A DRF Response object with paginated data and metadata.
    """
    return Response({
        'status': 'success',
        'data': data,
        'pagination': metadata
    }, status=status.HTTP_200_OK)


@log_pagination_info
def apply_pagination(request, queryset, serializer_class):
    """
    Apply pagination to a queryset and serialize the results.

    This function is a high-level utility that combines pagination and serialization.
    It's particularly useful in API views where you need to paginate and serialize data.

    Args:
        request (HttpRequest): The request object, used to extract pagination parameters.
        queryset (QuerySet): The Django queryset to paginate.
        serializer_class (Serializer): The DRF serializer class to use for serialization.

    Returns:
        Response: A DRF Response object with paginated and serialized data.

    Example:
        In a DRF view:
        def list(self, request):
            queryset = MyModel.objects.all()
            return apply_pagination(request, queryset, MyModelSerializer)
    """
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 10))

    paginated_data, metadata = paginate_queryset(queryset, page, page_size)
    serialized_data = serializer_class(paginated_data, many=True).data

    return get_paginated_response(serialized_data, metadata)


# Example usage
# if __name__ == "__main__":
#     # This is just for demonstration and won't run in a typical Django setup
#     class MockQuerySet:
#         def __init__(self, items):
#             self.items = items
#
#         def __len__(self):
#             return len(self.items)
#
#         def __getitem__(self, key):
#             return self.items[key]
#
#
#     mock_queryset = MockQuerySet([f"Item {i}" for i in range(100)])
#
#     paginated_data, metadata = paginate_queryset(mock_queryset, page=2, page_size=20)
#     print("Paginated Data:", paginated_data)
#     print("Metadata:", metadata)