class GExchanges:
    DOCUMENT_PROCESSING_EXCHANGE = "document_processing_exchange"
    DOCUMENT_PROCESSING_EXCHANGE_DLX = "document_processing_exchange_dlx"
    DOCUMENT_STATUS_EXCHANGE = "document_status_exchange"


class GQueues:
    DOCUMENT_PROCESSING_QUEUE = "document_processing_queue"
    DOCUMENT_PROCESSING_QUEUE_DLX = "document_processing_queue_dlx"
    DOCUMENT_STATUS_QUEUE = "document_status_queue"


class GRoutingKeys:
    DOCUMENT_PROCESSING_ROUTING_KEY = "document_processing_routing_key"
    DOCUMENT_STATUS_ROUTING_KEY = "document_status_routing_key"
