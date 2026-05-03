# Paste This Into Claude

Copy everything below this line and paste it as your first message in a new Claude conversation.

---

You are working with the **Project VOID standalone codon library**.

The library lives at: `void-codon-library/` inside the Project VOID GitHub repository at  
`https://github.com/umarlatif6-sketch/Project-void`

**Your entry points are:**

1. `void-codon-library/README.md` — what the package is and is not
2. `void-codon-library/PROOF.md` — the claim boundary and repo-level efficiency evidence
3. `void-codon-library/void_codon_library/catalog.py` — the full codon catalog and API
4. `void-codon-library/tests/test_catalog.py` — the regression test suite

**What you should understand immediately:**

- This package is a standalone extraction of the Project VOID codon system.
- It packages two catalogs: 15 platform codons and 10 SCL-LBN codons.
- It has a clean Python API: `get_codon`, `get_platform_codons`, `get_lbn_codons`, `codon_chain`, `all_codons`, `export_catalog`.
- It is validated: 3 regression tests pass, no errors.
- It does NOT include the full runtime, Chronicle, packet signing, or governance system.

**The core efficiency claim this library supports:**

75,155 tokens to orient a new agent → ~300 tokens via codon seed → 250× reduction.  
Source: `PROOF_OF_EFFICIENCY.md` in the repository root.

**The one-line positioning statement:**

> `void-codon-library` is the standalone packaged codon lookup layer for Project VOID —  
> the codon layer itself, not the whole organism.

**If you want to validate locally:**

```bash
git clone https://github.com/umarlatif6-sketch/Project-void
cd Project-void/void-codon-library
python3 -m unittest discover -s tests -p 'test_*.py'
```

**The distributable wheel is already built at:**

```
void-codon-library/dist/void_codon_library-0.1.0-py3-none-any.whl
void-codon-library/dist/void_codon_library-0.1.0.tar.gz
```

Private install path (preferred):

```bash
GH_TOKEN=<repo_read_token> ./void-codon-library/scripts/install_private.sh
```

Only if public release is explicitly approved, users install it with:

```bash
pip install void-codon-library
```

**Start by reading `catalog.py`.** That is the one file that contains everything the package delivers.
