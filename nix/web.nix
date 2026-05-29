# nix/web.nix — Hermes Web Dashboard (Vite/React) frontend build
{ pkgs, hermesNpmLib, ... }:
let
  src = ../apps;
  npmDeps = pkgs.fetchNpmDeps {
    inherit src;
    hash = "sha256-HV0aISBVjwbGqDj8qQynSxGFrrZDzuYAW3D3lB/x3zo=";
  };

  npm = hermesNpmLib.mkNpmPassthru { folder = "web"; attr = "web"; pname = "hermes-web"; };

  packageJson = builtins.fromJSON (builtins.readFile (src + "/dashboard/package.json"));
  version = packageJson.version;
in
pkgs.buildNpmPackage (npm // {
  pname = "hermes-web";
  inherit src npmDeps version;
  sourceRoot = "web";

  doCheck = false;

  buildPhase = ''
    npx tsc -b
    npx vite build --outDir dist
  '';

  installPhase = ''
    runHook preInstall
    cp -r dist $out
    runHook postInstall
  '';
})
