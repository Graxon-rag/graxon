class GExchanges:
    DOCUMENT_PROCESSING_EXCHANGE = "graxon_document_processing_exchange"
    DOCUMENT_PROCESSING_EXCHANGE_DLX = "graxon_document_processing_exchange_dlx"
    DOCUMENT_STATUS_EXCHANGE = "graxon_document_status_exchange"


class GQueues:
    DOCUMENT_PROCESSING_QUEUE = "graxon_document_processing_queue"
    DOCUMENT_PROCESSING_QUEUE_DLX = "graxon_document_processing_queue_dlx"
    DOCUMENT_STATUS_QUEUE = "graxon_document_status_queue"


class GRoutingKeys:
    DOCUMENT_PROCESSING_ROUTING_KEY = "graxon_document_processing_routing_key"
    DOCUMENT_STATUS_ROUTING_KEY = "graxon_document_status_routing_key"
