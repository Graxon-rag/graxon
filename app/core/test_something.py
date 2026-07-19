# from .processor.ocr.llamaparse_processor import LlamaCloudOCRProcessor
# # from .processor.text.json_processor import JsonProcessor
# from .processor.ocr.mistral_processor import MistralOCRProcessor
# from .processor.text.markdown_processor import MarkdownProcessor
from .processor.audio.groq_processor import GroqAduioProcessor
from dotenv import load_dotenv
import os
load_dotenv()


async def test_something():
    file_chunk_number = 0
    rag_chunk_index = 0
    results = []
    api_key = os.environ["GROQ_API_KEY"]

    while True:
        proc = GroqAduioProcessor(
            file_path="/home/avvk/Graxon/Graxon/graxon/test_documents/youtube_podcast_audio.mp3",
            filename="youtube_podcast_audio.mp3",
            api_key=api_key,
            file_chunk_number=file_chunk_number,
            rag_chunk_start_index=rag_chunk_index,
            segment_duration_min=2.5,
        )
        docs, next_rag_idx, is_last = await proc.process()
        results.append(docs)
        # docs → Vector DB + Neo4j

        if is_last:
            break
        file_chunk_number += 1
        rag_chunk_index = next_rag_idx

    return results

    # file_chunk_number = 0
    # rag_chunk_index = 0
    # results = []
    # api_key = os.environ["GLADIA_API_KEY"]

    # while True:
    #     proc = GladiaAudioProcessor(
    #         file_path="/home/avvk/Graxon/Graxon/graxon/test_documents/youtube_podcast_audio.mp3",
    #         filename="youtube_podcast_audio.mp3",
    #         api_key=api_key,
    #         file_chunk_number=file_chunk_number,
    #         rag_chunk_start_index=rag_chunk_index,
    #         segment_duration_min=2.5,
    #     )
    #     docs, next_rag_idx, is_last = await proc.process()
    #     results.append(docs)
    #     # docs → Vector DB + Neo4j

    #     if is_last:
    #         break
    #     file_chunk_number += 1
    #     rag_chunk_index = next_rag_idx

    # return results
    # file_chunk_number = 0
    # rag_chunk_index = 0
    # results = []
    # api_key = os.environ["ELEVENLABS_API_KEY"]

    # while True:
    #     proc = ElevenlabsAudioProcessor(
    #         file_path="/home/avvk/Graxon/Graxon/graxon/test_documents/youtube_podcast_audio.mp3",
    #         filename="youtube_podcast_audio.mp3",
    #         api_key=api_key,
    #         file_chunk_number=file_chunk_number,
    #         rag_chunk_start_index=rag_chunk_index,
    #         segment_duration_min=2.5,
    #         base_url="https://api.in.residency.elevenlabs.io"
    #     )
    #     docs, next_rag_idx, is_last = await proc.process()
    #     results.append(docs)
    #     # docs → Vector DB + Neo4j

    #     if is_last:
    #         break
    #     file_chunk_number += 1
    #     rag_chunk_index = next_rag_idx

    # return results

    # file_chunk_number = 0
    # rag_chunk_index = 0
    # results = []
    # api_key = os.environ["ASSEMBLYAI_API_KEY"]

    # while True:
    #     proc = AssemblyAudioProcessor(
    #         file_path="/home/avvk/Graxon/Graxon/graxon/test_documents/youtube_podcast_audio.mp3",
    #         filename="youtube_podcast_audio.mp3",
    #         api_key=api_key,
    #         file_chunk_number=file_chunk_number,
    #         rag_chunk_start_index=rag_chunk_index,
    #         segment_duration_min=2.5,
    #     )
    #     docs, next_rag_idx, is_last = await proc.process()
    #     results.append(docs)
    #     # docs → Vector DB + Neo4j

    #     if is_last:
    #         break
    #     file_chunk_number += 1
    #     rag_chunk_index = next_rag_idx

    # return results

    # file_chunk_number = 0
    # rag_chunk_index = 0
    # results = []
    # api_key = os.environ["DEEPGRAM_API_KEY"]

    # while True:
    #     proc = DeepgramAudioProcessor(
    #         file_path="/home/avvk/Graxon/Graxon/graxon/test_documents/youtube_podcast_audio.mp3",
    #         filename="youtube_podcast_audio.mp3",
    #         api_key=api_key,
    #         file_chunk_number=file_chunk_number,
    #         rag_chunk_start_index=rag_chunk_index,
    #         segment_duration_min=2.5,
    #     )
    #     docs, next_rag_idx, is_last = await proc.process()
    #     results.append(docs)
    #     # docs → Vector DB + Neo4j

    #     if is_last:
    #         break
    #     file_chunk_number += 1
    #     rag_chunk_index = next_rag_idx

    # return results

    # file_path = "/home/avvk/Graxon/Graxon/graxon/test_documents/some_page.pdf"
    # filename = "some_page.pdf"
    # api_key = os.environ["LLAMA_CLOUD_API_KEY"]
    # # api_key = os.environ["MISTRAL_API_KEY"]
    # start_page = 0
    # is_last_ocr_batch = False

    # rag_chunk_start_index = 0   # global — becomes each chunk's rag_chunk_number
    # all_docs = []

    # while not is_last_ocr_batch:
    #     ocr = LlamaCloudOCRProcessor(file_path, filename, api_key, start_page=start_page, max_pages_per_chunk=15)
    #     md_path, next_page, is_last_ocr_batch = await ocr.process()

    #     chunk_number = 0        # LOCAL — page index into THIS md_path's cache, must restart at 0 per file
    #     is_last_md_chunk = False

    #     while not is_last_md_chunk:
    #         mp = MarkdownProcessor(
    #             markdown_path=str(md_path),
    #             filename=filename,
    #             chunk_number=chunk_number,
    #             rag_chunk_start_index=rag_chunk_start_index,
    #             max_chunk_size_mb=0.01
    #         )
    #         docs, rag_chunk_start_index, is_last_md_chunk = await mp.process()
    #         all_docs.append(docs)
    #         chunk_number += 1

    #     start_page = next_page

    # return all_docs

    # print("Loading processor")
    # file_path = "/home/avvk/Graxon/Graxon/graxon/test_documents/nested_test.json"
    # filename = "nested_test.json"

    # max_chunk_size_mb = 10.0      # Adjust as needed for your database limits
    # objects_per_buffer = 30      # Number of JSON objects to read per iteration

    # result = []
    # rag_chunk_start_index = 0
    # start_object = 0              # 0-based start (JSON doesn't have headers to skip)
    # iteration = 0                 # Tracks loop runs 
    # is_last = False

    # # The loop runs until process() reports is_last=True for the file
    # while not is_last:
    #     processor = JsonProcessor(
    #         file_path=file_path,
    #         filename=filename,
    #         start_object=start_object,
    #         rag_chunk_start_index=rag_chunk_start_index,
    #         objects_per_buffer=objects_per_buffer,
    #         max_chunk_size_mb=max_chunk_size_mb
    #         # group_size and max_group_size will use the defaults from the class
    #     )

    #     # Await the processing of this specific chunk
    #     docs, next_rag_chunk_start_index, is_last = await processor.process()

    #     # Log the progress
    #     print(f"iteration={iteration} (start_object={start_object}) -> {len(docs)} docs, "
    #           f"rag_chunk_start_index {rag_chunk_start_index} -> {next_rag_chunk_start_index}, "
    #           f"is_last={is_last}")

    #     # Update indices for the next batch
    #     rag_chunk_start_index = next_rag_chunk_start_index

    #     # Use extend to keep a flat list of LangChain Documents
    #     result.extend(docs) 

    #     # Advance the sliding window down the JSON array/objects
    #     start_object += objects_per_buffer
    #     iteration += 1

    # print(f"\n✅ Finished processing {filename}!")
    # return result

    # file_path = "/home/avvk/Graxon/Graxon/graxon/test_documents/test.csv"
    # filename = "test.csv"

    # max_chunk_size_mb = 50.0      # Adjust as needed for your database limits
    # rows_per_io_buffer = 500      # Number of rows to read per iteration

    # result = []
    # rag_chunk_start_index = 0
    # start_row = 1                 # 1-based start (assuming row 0 is header)
    # iteration = 0                 # Tracks loop runs 
    # is_last = False

    # # The loop runs until process() reports is_last=True for the file
    # while not is_last:
    #     processor = CSVProcessor(
    #         file_path=file_path,
    #         filename=filename,
    #         start_row=start_row,
    #         rag_chunk_start_index=rag_chunk_start_index,
    #         rows_per_io_buffer=rows_per_io_buffer,
    #         max_chunk_size_mb=max_chunk_size_mb
    #         # group_size and max_group_size will use the defaults from the class
    #     )

    #     # Await the processing of this specific chunk
    #     docs, next_rag_chunk_start_index, is_last = await processor.process()

    #     # Log the progress
    #     print(f"iteration={iteration} (start_row={start_row}) -> {len(docs)} docs, "
    #           f"rag_chunk_start_index {rag_chunk_start_index} -> {next_rag_chunk_start_index}, "
    #           f"is_last={is_last}")

    #     # Update indices for the next batch
    #     rag_chunk_start_index = next_rag_chunk_start_index

    #     # Use extend to keep a flat list of LangChain Documents
    #     result.extend(docs) 

    #     # Advance the sliding window down the CSV
    #     start_row += rows_per_io_buffer
    #     iteration += 1

    # print(f"\n✅ Finished processing {filename}!")
    # return result

    # sheet = 0
    # file_path = "/home/avvk/Graxon/Graxon/graxon/test_documents/test_multisheet.xlsx"
    # filename = "test_multisheet.xlsx"
    # max_chunk_size_mb = 50  # Adjust as needed for Excel
    # rows_per_io_buffer = 500  # Number of rows to read per iteration

    # result = []
    # rag_chunk_start_index = 0
    # start_row = 1             # 1-based start (assuming row 0 is header)
    # iteration = 0             # Tracks loop runs (similar to chunk_number)
    # is_last = False

    # # The loop runs until process() reports is_last=True for the sheet
    # while not is_last:
    #     processor = ExcelProcessor(
    #         file_path=file_path,
    #         filename=filename,
    #         start_row=start_row,
    #         rag_chunk_start_index=rag_chunk_start_index,
    #         sheet=sheet,
    #         rows_per_io_buffer=rows_per_io_buffer,
    #         max_chunk_size_mb=max_chunk_size_mb
    #     )

    #     docs, next_rag_chunk_start_index, is_last = await processor.process()

    #     print(f"iteration={iteration} (start_row={start_row}) -> {len(docs)} docs, "
    #           f"rag_chunk_start_index {rag_chunk_start_index} -> {next_rag_chunk_start_index}, "
    #           f"is_last={is_last}")

    #     # Update indices for the next batch
    #     rag_chunk_start_index = next_rag_chunk_start_index
    #     result.append(docs)

    #     # Advance the sliding window down the spreadsheet
    #     start_row += rows_per_io_buffer
    #     iteration += 1

    # return result

    # max_chunk_size_mb = 0.01
    # markdown_path = "/home/avvk/Graxon/Graxon/graxon/test_documents/mistal_out.md"
    # filename = "mistal_out.md"

    # result = []
    # rag_chunk_start_index = 0
    # chunk_number = 0
    # is_last = False

    # # Unlike the raw byte-window MarkdownProcessor, total page count here isn't
    # # known upfront -- it depends on how the whole file parses (tables, text
    # # splitting, etc.), so the loop runs until process() reports is_last=True,
    # # rather than a precomputed range(total_chunks).
    # while not is_last:
    #     processor = MarkdownProcessor(
    #         markdown_path=markdown_path,
    #         filename=filename,
    #         chunk_number=chunk_number,
    #         rag_chunk_start_index=rag_chunk_start_index,
    #         max_chunk_size_mb=max_chunk_size_mb,
    #     )
    #     docs, next_rag_chunk_start_index, is_last = await processor.process()

    #     print(f"chunk_number={chunk_number} -> {len(docs)} docs, "
    #           f"rag_chunk_start_index {rag_chunk_start_index} -> {next_rag_chunk_start_index}, "
    #           f"is_last={is_last}")

    #     rag_chunk_start_index = next_rag_chunk_start_index
    #     result.append(docs)
    #     chunk_number += 1

    # return result

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
