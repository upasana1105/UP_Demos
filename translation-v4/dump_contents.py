import fitz
import sys

doc = fitz.open('/Users/upasanapati/shrinkAI experiment/Antigravity_Experiments/UP_Demos/translation-v3/uploads/5g-edge-computing-value-opportunity_de.pdf')
page = doc[0]

contents = page.get_contents()
print(f"Contents XREFs: {contents}")

for i, xref in enumerate(contents):
    stream = page.read_contents() # Read all combined
    print(f"Combined stream length: {len(stream)}")
    # Let's print the first 500 and last 500 chars
    print("First 500 chars:")
    print(stream[:500].decode(errors='ignore'))
    print("\nLast 500 chars:")
    print(stream[-500:].decode(errors='ignore'))
    
    # Let's check specific streams if multiple
    stream_parts = []
    for x in contents:
        stream_parts.append(doc.xref_stream(x))
    
    for j, part in enumerate(stream_parts):
        print(f"\nPart {j} (XREF {contents[j]}) length: {len(part)}")
        print(f"Part {j} snippet:")
        print(part[:200].decode(errors='ignore'))
