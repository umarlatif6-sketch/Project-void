from void_sdk import VoidSDK

sdk = VoidSDK()

sdk.track(
    entity="user:demo-001",
    condition="frequency:432hz formation_score:0.87",
    action="encode",
    codon="voidecho",
    meta={"chars": 420},
)

export = sdk.export_records(
    fmt="jsonl",
    codon="voidecho",
    limit=100,
    file_path="void_events.jsonl",
)

print(export)
