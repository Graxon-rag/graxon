from .processor.markdown_processor import MarkdownProcessor


async def test_something():
    print("Loading processor")
    max_chunk_size_mb = 0.01
    markdown_path = "/home/avvk/Graxon/Graxon/graxon/test_documents/mistal_out.md"
    filename = "mistal_out.md"

    result = []
    rag_chunk_start_index = 0
    chunk_number = 0
    is_last = False

    # Unlike the raw byte-window MarkdownProcessor, total page count here isn't
    # known upfront -- it depends on how the whole file parses (tables, text
    # splitting, etc.), so the loop runs until process() reports is_last=True,
    # rather than a precomputed range(total_chunks).
    while not is_last:
        processor = MarkdownProcessor(
            markdown_path=markdown_path,
            filename=filename,
            chunk_number=chunk_number,
            rag_chunk_start_index=rag_chunk_start_index,
            max_chunk_size_mb=max_chunk_size_mb,
        )
        docs, next_rag_chunk_start_index, is_last = await processor.process()

        print(f"chunk_number={chunk_number} -> {len(docs)} docs, "
              f"rag_chunk_start_index {rag_chunk_start_index} -> {next_rag_chunk_start_index}, "
              f"is_last={is_last}")

        rag_chunk_start_index = next_rag_chunk_start_index
        result.append(docs)
        chunk_number += 1

    return result

    # print("Loading processor")
    # max_chunk_size_mb = 0.01
    # file_path = "/home/avvk/Graxon/Graxon/graxon/app/core/workflow/lgraph/document_inject_graph.py"
    # file_size = os.path.getsize(file_path)

    # io_buffer_size = int(max_chunk_size_mb * 1024 * 1024)
    # total_chunks = -(-file_size // io_buffer_size)  # ceiling division
    # result = []
    # rag_chunk_start_index = 0
    # for chunk_number in range(total_chunks):
    #     processor = ProcessorFactory.get_processor(file_path, "code", "inject_graph.py", chunk_number=chunk_number, rag_chunk_start_index=rag_chunk_start_index, max_chunk_size_mb=max_chunk_size_mb)
    #     docs, index, _ = await processor.process()
    #     rag_chunk_start_index = index
    #     result.append(docs)
    # return result
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
