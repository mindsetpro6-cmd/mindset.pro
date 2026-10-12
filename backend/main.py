import os
from functools import lru_cache

from supabase import Client, create_client

@lru_cache(maxsize=1)
def obter_cliente_supabase() -> Client:
url = os.getenv("SUPABASE_URL")
chave = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

```
if not url or not chave:
    raise RuntimeError(
        "As variáveis do Supabase não estão configuradas."
    )

return create_client(url, chave)
```
