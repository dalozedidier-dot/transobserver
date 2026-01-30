Dispatch all modules (simple)

But:
Tu cliques "Run workflow" une fois, et ça déclenche les workflows ciblés dans les 5 repos.
Ce workflow ne télécharge rien et n'attend pas la fin. Il fait seulement des dispatch.

Fichiers:
- .github/workflows/dispatch_all_modules.yml
- scripts/dispatch_all.py
- targets.yml

Pré-requis:
- Secret GH_PAT dans le repo qui héberge ce workflow
- GH_PAT doit avoir Actions: Read and write sur les repos ciblés

Où lancer (GitHub web):
Repo orchestrateur -> Actions -> "Dispatch all modules" -> Run workflow

Ajuster:
- targets.yml : mets les bons fichiers workflow (ci.yml, smoke.yml, etc.)
  ou remplace par "id:" si tu veux zéro ambiguïté.

Sortie:
- artefact "dispatch_out" contenant _dispatch_out/summary.json
