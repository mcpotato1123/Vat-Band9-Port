$ErrorActionPreference = 'Stop'
$sign = Join-Path $PSScriptRoot '..\sign'
$sign = [System.IO.Path]::GetFullPath($sign)
New-Item -ItemType Directory -Force -Path $sign | Out-Null

$rsa = [System.Security.Cryptography.RSA]::Create(2048)
$subject = 'CN=Vat Band9 Port, O=Unofficial Port, C=CN'
$req = [System.Security.Cryptography.X509Certificates.CertificateRequest]::new(
    $subject,
    $rsa,
    [System.Security.Cryptography.HashAlgorithmName]::SHA256,
    [System.Security.Cryptography.RSASignaturePadding]::Pkcs1)

$cert = $req.CreateSelfSigned(
    [DateTimeOffset]::UtcNow.AddDays(-1),
    [DateTimeOffset]::UtcNow.AddDays(3650))

# private key (PKCS#8 PEM) — aiot expects a standard PEM private key
$keyPem = $rsa.ExportPkcs8PrivateKeyPem()
[System.IO.File]::WriteAllText((Join-Path $sign 'private.pem'), $keyPem)

# certificate PEM
$certPem = [System.Security.Cryptography.PemEncoding]::Write(
    'CERTIFICATE', [System.ReadOnlySpan[byte]]$cert.RawData)
[System.IO.File]::WriteAllText((Join-Path $sign 'certificate.pem'), $certPem)

Write-Output ("subject  : " + $cert.Subject)
Write-Output ("notAfter : " + $cert.NotAfter.ToString('yyyy-MM-dd'))
Write-Output ("files    : " + (Get-ChildItem $sign | ForEach-Object { $_.Name + '(' + $_.Length + 'B)' }) -join ' ')
