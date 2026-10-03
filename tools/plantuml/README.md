# PlantUML (not committed)

`tools/puml_render.py` needs `tools/plantuml/plantuml.jar` (PlantUML 1.2026.8, Java ≥ 11, built-in Smetana layout,
no Graphviz). Fetch and verify:

```bash
cd tools/plantuml
V=1.2026.8
curl -sfLo plantuml.jar https://repo1.maven.org/maven2/net/sourceforge/plantuml/plantuml/$V/plantuml-$V.jar
echo "$(curl -sfL https://repo1.maven.org/maven2/net/sourceforge/plantuml/plantuml/$V/plantuml-$V.jar.sha1)  plantuml.jar" | sha1sum -c
```
