# Set the root directory where your original files are located
$sourceDir = "C:\git_hub\samplicity\samplicity"

# Set the output directory where renamed files will be copied
$outputDir = "C:\git_hub\claude"

# Create the output directory if it doesn't exist
if (!(Test-Path -Path $outputDir)) {
    New-Item -ItemType Directory -Force -Path $outputDir
}

# Get all .py files recursively from the source directory
$files = Get-ChildItem -Path $sourceDir -Recurse -File -Filter "*.py"

foreach ($file in $files) {
    # Get the relative path from the source directory
    $relativePath = $file.FullName.Substring($sourceDir.Length + 1)
    
    # Split the path into folders
    $folders = $relativePath.Split([IO.Path]::DirectorySeparatorChar)
    
    # Check if the file is in the base directory
    if ($folders.Length -eq 1) {
        # If in base directory, just use the original filename
        $newName = $file.Name
    } else {
        # Join all folders except the last one (which is the filename)
        $newPrefix = $folders[0..($folders.Length - 2)] -join " - "
        
        # Create the new filename
        $newName = "$newPrefix - $($file.Name)"
    }
    
    # Create the full path for the new file
    $newPath = Join-Path -Path $outputDir -ChildPath $newName
    
    # Copy the file to the new location with the new name
    Copy-Item -Path $file.FullName -Destination $newPath -Force
    
    # Output the copying action
    Write-Host "Copied and renamed: $($file.FullName) to $newPath"
}

Write-Host "Process complete! All .py files have been copied and renamed in the output directory."