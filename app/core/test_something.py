from .processor.processor_factory import ProcessorFactory
import os


async def test_something():
    # print("Loading processor")
    # max_chunk_size_mb = 0.01
    # file_path = "/home/avvk/Graxon/Graxon/graxon/README.md"
    # file_size = os.path.getsize(file_path)

    # io_buffer_size = int(max_chunk_size_mb * 1024 * 1024)
    # total_chunks = -(-file_size // io_buffer_size)  # ceiling division
    # result = []
    # rag_chunk_start_index = 0
    # for chunk_number in range(total_chunks):
    #     processor = ProcessorFactory.get_processor(file_path, "md", "README.md", chunk_number=chunk_number, rag_chunk_start_index=rag_chunk_start_index, max_chunk_size_mb=max_chunk_size_mb)
    #     docs, index, _ = await processor.process()
    #     rag_chunk_start_index = index
    #     result.append(docs)
    # return result
    # max_chunk_size_mb = 0.001
    # file_path = "/home/avvk/Graxon/Graxon/graxon/test_documents/vipin.txt"
    # file_size = os.path.getsize(file_path)

    # io_buffer_size = int(max_chunk_size_mb * 1024 * 1024)
    # total_chunks = -(-file_size // io_buffer_size)  # ceiling division
    # result = []
    # rag_chunk_start_index = 0
    # for chunk_number in range(total_chunks):
    #     processor = ProcessorFactory.get_processor(file_path, "text", "vipin.txt", chunk_number=chunk_number, rag_chunk_start_index=rag_chunk_start_index, max_chunk_size_mb=max_chunk_size_mb)
    #     docs, index, _ = await processor.process()
    #     rag_chunk_start_index = index
    #     result.append(docs)
    # return result
    pass
