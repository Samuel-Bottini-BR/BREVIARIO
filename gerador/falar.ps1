# Le em voz alta o que se lhe der.
#
# Serve para o senhor poder continuar a pintar enquanto eu vou dando
# conta do trabalho. A voz e a Maria, a unica portuguesa instalada.
#
#   powershell -File gerador\falar.ps1 -Texto "o que dizer"
#   powershell -File gerador\falar.ps1 -Ficheiro recado.txt
#
# O texto vem de um ficheiro quando for comprido: a linha de comandos
# estraga os acentos, e um breviario sem acentos le-se mal.

param(
    [string]$Texto = '',
    [string]$Ficheiro = '',
    [int]$Velocidade = 1,
    [int]$Volume = 100
)

Add-Type -AssemblyName System.Speech
$voz = New-Object System.Speech.Synthesis.SpeechSynthesizer

# A portuguesa primeiro; se nao houver, a que houver.
$portuguesa = $voz.GetInstalledVoices() |
    Where-Object { $_.VoiceInfo.Culture.Name -like 'pt*' } |
    Select-Object -First 1
if ($portuguesa) { $voz.SelectVoice($portuguesa.VoiceInfo.Name) }

$voz.Rate = $Velocidade
$voz.Volume = $Volume

if ($Ficheiro -and (Test-Path $Ficheiro)) {
    $Texto = [System.IO.File]::ReadAllText($Ficheiro, [System.Text.Encoding]::UTF8)
}
if (-not $Texto) { exit }

# O que nao se le bem em voz alta: marcas de tabela, cabecalhos de
# markdown, e as barras dos numeros.
$Texto = $Texto -replace '\|', ', ' -replace '#', '' -replace '\*', ''
$Texto = $Texto -replace '`', '' -replace '—', ', '
$Texto = $Texto -replace '\s+', ' '

$voz.Speak($Texto)
