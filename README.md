# Fortitoken_Reissue

Mass reissue of Fortitokens for LDAP users on FortiAuthenticator

Requires REST API administrator account and access key

By default skips users that have "OU=Disabled" in the DN, see the SkipIf variable inside

Usage: ./Fortitoken_Reissue.py \<FortiAuthIP\> \<ApiAdminUsername\> \<ApiAdminKey\>
