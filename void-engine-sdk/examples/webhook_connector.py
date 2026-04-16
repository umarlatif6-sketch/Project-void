from void_sdk import VoidSDK

sdk = VoidSDK()

response = sdk.send_webhook(
    url="https://example.com/void/events",
    entity="user:demo-001",
    condition="frequency:432hz formation_score:0.87",
    action="encode",
    codon="voidecho",
    meta={"chars": 420, "source": "example"},
)

print(response)
