from huggingface_hub import model_info
try:
    m = model_info('pb11-x/reality-detector-model')
    print('EXISTS')
    print(m.id)
    print(m.sha)
except Exception as e:
    print('NOT_FOUND')
    print(str(e))
